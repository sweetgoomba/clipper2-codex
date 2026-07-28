# AI 숏폼 디렉터 품질 입력·생성 이력·영상 제작 경로 — 설계

> 작성일: 2026-07-27
> 정본 위치: `.codex/design`
> 대상 레포: `desktop/clipper_angular`, `desktop/clipper_nestjs`, `web/clipper_web_api`,
> `web/clipper_web_admin`
> 성격: 크로스 레포 기능 설계. 승인된 화면 목업과 2026-07-27 사용자 결정을 정본화한다.
> 후속: 이 설계의 사용자 검토 승인 뒤 구현 계획을 별도로 작성한다.

## 1. 배경

현재 AI 숏폼 디렉터는 사용자가 한 화면에서 입력을 구성하고, 전략과 영상 계획을
순서대로 생성하는 구조다. 전략·상세 영상 설계는 기본 `gpt-4.1`, 이미지 생성은
`gemini-3.1-flash-image`, 영상 생성은 `veo-3.1-fast-generate-preview`를 사용한다.
로컬 프로젝트 상태는 `CLIPPER_DATA_DIR/shortform-director/projects.json`에 저장하지만,
다음 품질 경계는 아직 연결돼 있지 않다.

- 운영 프로필을 기준으로 최신 시장을 자동 조사하는 경로
- Google Trends, 네이버, YouTube를 함께 쓰는 다중 출처 조사
- 조사 결과에서 여러 주제를 찾고 주제마다 최소 10개의 영상 후보를 만드는 경로
- 원본 수집 데이터부터 최종 장면까지의 생성 근거 추적
- LLM 요청·응답·검증·탈락 이유를 로컬 JSON으로 보존하는 실행 이력
- 장면 목적에 맞는 실제 자료·도식·생성 이미지·생성 영상을 선택하는 시각 연출
- 실제 공급자를 사용한 결과물 품질 비교

최근 입력 검증용 fixture는 실험 구조를 검토하기 위한 자료이지 최신 시장 조사 결과가
아니다. 새 설계는 특정 인물·제품·키워드를 정답으로 고정하지 않는다. 운영 프로필과
실행 시점의 실제 조사 결과가 주제와 영상 후보를 결정한다.

## 2. 목표

사용자가 복잡한 자료 입력을 하지 않아도 다음 세로 흐름이 실제로 완주돼야 한다.

```text
운영 프로필 선택
→ 다중 출처 일회성 최신 조사
→ 근거가 연결된 주제 여러 개
→ 선택 주제의 영상 후보 최소 10개
→ 선택 후보의 상세 장면 설계
→ 장면별 적합한 시각 표현과 자료 준비
→ 내레이션·자막·이미지·영상 합성
→ Motion Canvas 완성 영상
→ 조사부터 결과물까지의 근거·과정 열람
```

성공 조건은 다음과 같다.

1. 지속 수집 이력이 없어도 한 번의 조사로 현재성 있는 주제를 찾을 수 있다.
2. Google Trends·네이버·YouTube 중 어느 하나도 단순 보조 출처로 강등하지 않는다.
3. 조사 자료, 정규화 결과, LLM 입력·응답, 탈락·검증 결과를 로컬 JSON으로 남긴다.
4. UI의 각 주제·영상 후보·장면에서 그 결과의 근거와 생성 과정을 역추적할 수 있다.
5. 사용자는 기본 흐름에서 자료를 직접 첨부하지 않아도 된다.
6. 영상 후보를 세 개로 제한하지 않고 실행당 최소 10개를 제공한다.
7. 장면 자료는 고정 우선순위로 찾지 않고, 장면의 전달 목적에 따라 종류를 먼저 정한다.
8. 모델·공급자 선택은 실제 한국어 결과물, 비용, 지연, 실패율 비교로 갱신할 수 있다.
9. AI Director의 조사·기획·미디어·품질 검사에는 Clipper 크레딧을 차감하지 않는다.

## 3. 1차 범위와 제외 범위

### 3.1 포함

- 운영 프로필 CRUD
- 플러그인 내부 임시 서브 페이지 사이드바
- Google Trends Trending Now RSS·CSV 수집
- 네이버 뉴스·웹·블로그 검색
- 네이버 데이터랩 검색어 추이 조회
- YouTube의 독립적인 인기·관련 영상 수집과 댓글·영상 형식 분석
- 공식 사이트·보도자료 자동 탐색
- 다중 출처 증거 정규화·중복 제거·최신성 판정
- 근거가 연결된 주제 생성
- 주제별 영상 후보 최소 10개 생성
- 선택 후보의 상세 장면 설계
- 장면별 시각 표현 결정과 자료 준비
- 현재 공급자와 신규 후보 모델 비교
- 조사·LLM·미디어·렌더 실행의 로컬 JSON 저장
- 결과별 `근거·과정` 패널과 전체 `실행 기록` 페이지

### 3.2 제외

- Google Trends 알파 API
  - 사용자가 알파 테스터 선정 사실을 알리기 전까지 호출·구현하지 않는다.
- Google Trends HTML 페이지 추출
  - RSS·CSV와 네이버 데이터랩의 실측 한계가 확인되기 전까지 보류한다.
- 장기간 지속 수집을 전제로 한 Vira 의존
  - Vira snapshot을 추후 입력으로 연결할 수 있지만 이번 흐름의 필수 조건이 아니다.
- 이전 영상의 승인·수정·실패를 다음 영상에 자동 학습시키는 기능
- 사전 보유 자료를 먼저 뒤지는 미디어 공급 경로
- 사용자 파일 첨부를 필수 입력으로 요구하는 흐름
- 특정 테스트 키워드·연예인·제품을 결과로 고정하는 fixture
- 웹 서버에 조사·생성 콘텐츠의 별도 영속 DB를 만드는 작업

## 4. 확정 결정

| # | 결정 |
|---|---|
| D1 | 최신 조사는 Google Trends·네이버·YouTube의 병렬 발견 결과를 합치는 구조로 한다. |
| D2 | YouTube `order=date` 무차별 수집은 1차 경로에서 제외한다. |
| D3 | Google Trends는 Trending Now RSS·CSV만 사용하고 알파 API와 HTML 추출은 보류한다. |
| D4 | 한국 검색 관심도는 등록된 네이버 데이터랩 API를 사용한다. |
| D5 | 공식 자료는 백엔드가 자동 탐색하며 사용자 첨부는 선택적 보강으로만 둔다. |
| D6 | 영상 후보는 원본 후보를 넉넉히 만든 뒤 중복·저품질을 제거하고 최소 10개를 보장한다. |
| D7 | LLM·공급자 후보는 §12의 초기 구성을 사용하고 실제 테스트 결과로 바꾼다. |
| D8 | 구조화 데이터의 로컬 SoT는 `CLIPPER_DATA_DIR` 아래 JSON 파일이다. |
| D9 | 원본 수집·정규화·LLM 요청/응답·검증·탈락 결과를 덮어쓰지 않고 실행별로 보존한다. |
| D10 | 각 결과에는 상위 입력 ID를 기록해 출처부터 완성 장면까지 역추적 가능하게 한다. |
| D11 | UI는 기본 화면을 단순하게 유지하고 `근거·과정` 패널과 `실행 기록`에서 상세를 노출한다. |
| D12 | 장면 미디어는 고정 fallback 순서가 아니라 장면별 커뮤니케이션 목적을 기준으로 결정한다. |
| D13 | 렌더 경로는 Motion Canvas만 대상으로 한다. |
| D14 | 공급자 credential은 Electron 환경 파일·빌드 산출물·로컬 실행 JSON에 넣지 않고, 기존 관리자 페이지에서 등록해 웹 API의 암호화 DB에만 보관한다. |
| D15 | 데스크톱은 기존 사용자 인증으로 웹 API의 AI Director 전용 공급자 프록시를 호출한다. 이 경로는 operation run·크레딧 차감·환불을 사용하지 않으며, 웹 API는 credential 자체를 데스크톱에 반환하지 않는다. |
| D16 | 영상 렌더는 기존 공용 작업 큐를 사용하고, 성공한 MP4는 기존 `projects.json` 기반 보관함과 파일 재생 경로에 등록한다. |

## 5. 사용자 흐름과 페이지

AI Director 플러그인의 최상위 진입점은 유지하고, 내부에 임시 사이드바를 둔다. 장차
플러그인 공통 내부 탐색 UI가 생기면 공통 컴포넌트로 교체할 수 있으나 이번 구현에서
그 공통 시스템까지 만들지 않는다.

### 5.1 페이지 구성

| 페이지 | 역할 |
|---|---|
| `프로필` | 운영 프로필 목록·생성·수정·복제·삭제 |
| `아이디어 찾기` | 새 조사 시작, 조사 진행 상태, 최신 조사 결과와 주제 |
| `영상 후보` | 선택 주제에서 생성된 최소 10개의 영상 후보 |
| `영상 제작` | 선택 후보의 내레이션·장면·시각 표현·자료·음성·렌더 준비 |
| `완성 영상` | 결과 영상, 품질 검사, 전체 제작 기록 |
| `실행 기록` | 조사·LLM·미디어·렌더 실행과 원본 JSON의 전체 탐색 |

프로필 삭제는 기존 실행의 계보를 끊는 물리 삭제로 처리하지 않는다. 활성 목록에서는
숨기되 삭제 시각이 있는 보관 상태로 전환하고, 모든 실행은 시작 시점의
`profile-snapshot.json`을 별도로 동결한다.

### 5.2 새 영상 시작

1. 사용자가 `새 영상 시작`을 누른다.
2. 운영 프로필을 고른다.
3. 키워드는 선택적으로 입력한다.
   - 비어 있으면 프로필 분야 전체를 조사한다.
   - 입력하면 해당 키워드를 중심으로 조사하되 관련 신호를 자동 확장한다.
4. 자료 첨부는 고급 선택 기능으로만 제공한다.
5. `조사 시작`으로 `ResearchRun`을 만든 뒤 `아이디어 찾기`로 이동한다.

사용자는 Vira JSON, 공식 자료, 시장 데이터 등을 직접 붙여넣지 않아도 기본 흐름을
완주할 수 있어야 한다.

## 6. 입력 축의 현재 범위

이번 범위의 입력은 다음 다섯 종류로 정리한다.

| 축 | 생성 방식 |
|---|---|
| Profile | 사용자가 관리하는 운영 목적·시청자·톤·금지사항 |
| Source | 공식 사이트·보도자료·권위 자료를 백엔드가 자동 탐색 |
| Audience | 검색 표현·댓글·질문·오해·불편을 조사에서 추출 |
| Market | Google Trends·네이버·YouTube의 실행 시점 시장 snapshot |
| Reference | YouTube 등에서 관찰한 훅·전개·장면·리듬 패턴 |

과거 영상 피드백의 자동 전이는 이번 구현에 포함하지 않는다.

## 7. 다중 출처 조사 아키텍처

### 7.1 핵심 원칙

Google Trends·네이버·YouTube는 발견 우선순위를 갖지 않는다. 각 수집기가 독립적으로
신호를 만들고 `SignalMerger`가 합친다. 따라서 다음이 모두 가능하다.

- YouTube에서만 강하게 보이는 주제가 생성된다.
- 뉴스에서 처음 등장한 사건이 주제가 된다.
- Trending Now에 있지만 YouTube 영상이 아직 적은 주제가 생성된다.
- 여러 출처에 동시에 나타난 주제가 더 높은 증거 다양성을 얻는다.

네이버 데이터랩은 두 번 사용할 수 있다.

1. 프로필 기본 키워드 묶음을 조사 시작과 동시에 조회한다.
2. 다른 출처에서 새로 발견한 키워드 묶음을 합친 뒤 추가 조회한다.

### 7.2 조사 흐름

```text
OperatingProfile snapshot
        ↓
QueryPlanner
        ├─ Google Trends Trending Now RSS/CSV
        ├─ NAVER news/web/blog
        ├─ YouTube search/videos/comments
        └─ NAVER DataLab initial keyword groups
                ↓
       Raw SourceFetch records
                ↓
Normalizer → Dedupe → Freshness policy
                ↓
 Trends / News / Video / Audience / Reference signals
                ↓
SignalMerger + TopicClusterer
                ↓
새로 발견한 keyword group의 DataLab 보강
                ↓
OfficialSourceFinder + FactVerifier
                ↓
TopicSynthesizer
                ↓
TopicValidator
                ↓
Frozen ResearchSnapshot
```

### 7.3 QueryPlanner

입력:

- 프로필 분야·대상 시청자·지역·언어
- 선택적 사용자 키워드
- 기본 최신성 기간
- 직전 성공 실행의 검색어는 사용자가 명시적으로 재사용할 때만 입력

출력:

- 핵심 검색어
- 동의어·띄어쓰기·영문명·별칭
- 질문·오해·비교·문제 해결 검색어
- 인물·브랜드·제품·사건 검색어
- 출처별 검색어와 기간

LLM이 검색어 확장을 도울 수 있지만 검색어가 사실의 근거가 되지는 않는다.

### 7.4 Google Trends 수집

기간 계약은 다음 네 값으로 닫는다.

```ts
type GoogleTrendsWindow = '4h' | '24h' | '48h' | '7d';

const GOOGLE_TRENDS_HOURS = {
  '4h': 4,
  '24h': 24,
  '48h': 48,
  '7d': 168,
} as const;
```

사용:

- Trending Now RSS
  - 자동 조사 경로다. 한 research run은 같은 고정 `asOf`로 4시간·24시간·48시간·7일
    feed를 각각 호출하고 호출마다 별도 `SourceFetchRecordV1`을 만든다.
  - `window`는 요청한 feed 범위이며 항목의 나이나 `pubDate`에서 추론하지 않는다.
  - XML은 namespace URI `https://trends.google.com/trending/rss`를 기준으로 읽어
    prefix가 달라도 같은 URI면 허용하고, 같은 local name이라도 URI가 다르면 거부한다.
    반복 news item은 모두 보존한다.
  - DOCTYPE과 ENTITY **선언**은 fail closed한다. XML 기본 entity reference는
    namespace-aware parser가 정상 decode한다.
- Trending Now CSV
  - Google Trends UI의 공식 내보내기 형식 parser를 보조 경계로 제공한다.
  - 문서화된 안정적 다운로드 URL이 없는 동안 UI HTML이나 내부 RPC를 추출해 자동화하지
    않는다. CSV 부재는 기본 RSS 조사를 막지 않고, 사용자에게 CSV 첨부를 필수로
    요구하지 않는다.
  - C1의 CSV parser는 parsed DTO만 반환한다. 실제 network 호출이 아니므로 가짜 URL,
    HTTP status, latency를 채운 `SourceFetchRecordV1`을 만들지 않는다.
  - C1이 필수 지원하는 sanitized 공식 header는 영문
    `Trends, Search volume, Started, Ended, Trend breakdown`이다. 한국어 header
    alias는 실제 sanitized export를 확보해 exact fixture로 고정하기 전에는 추측해
    추가하지 않는다.
  - 별도 status 열을 전제하지 않는다. trim한 `Ended`가 nonblank면 `ended`,
    `Ended`가 blank이고 trim한 `Started`가 nonblank면 `active`, 둘 다 blank면
    `unknown`이다. Started/Ended `sourceText`는 항상 보존한다.
  - optional `started.at`/`ended.at`은 sanitized official fixture에서 실제 확인한
    timezone-bearing absolute 또는 relative 문법만 exact parser/test로 추가할 수
    있다. 현재 확보한 CSV capture가 없으므로 C1 필수 범위에서 해석 시각을 추측하거나
    assertion하지 않는다. 실제 status 열도 capture 뒤 fixture-backed exact alias로만
    보조 입력에 추가할 수 있다.

저장:

- RSS의 완전 수신·UTF-8 decode·redaction 뒤 저장 원문, stored-body checksum,
  파싱한 항목
- CSV parser의 파싱 결과. 이후 실제 import 기능이 생기면 그 경계가 별도 user-source
  artifact와 원본 보존을 책임진다.
- 검색량 bucket의 `sourceText`와 선택적 lower bound, 시작·종료 `sourceText`와
  선택적 해석 시각, 활성 상태
- CSV trend breakdown의 관련 검색어와 RSS의 반복 news item
- 출처가 제공하지 않거나 의미가 불명확한 성장률은 `0`으로 만들지 않고 생략한다.

사용하지 않음:

- 알파 API
- UI HTML 추출
- 비공식·미문서 endpoint

### 7.5 네이버 수집

검색 API:

- 뉴스
- 웹 문서
- 블로그

DataLab:

- 프로필 핵심 검색어 묶음
- 새로 발견된 연관 검색어 묶음
- 최근 기간과 직전 비교 기간
- 가능한 경우 모바일·대상 연령 등 프로필 조건

네이버 데이터랩의 상대 지수는 절대 검색량으로 표현하지 않는다. UI에도 `검색량`이
아니라 `검색 관심도 변화`로 표시한다.

news/web/blog와 initial/discovered DataLab은 서로 다른 source port 호출이다. 모든
호출 input은 동결한 `researchRunId`, `asOf`, 1 이상의 `attempt`, run-level
`AbortSignal`과 해당 query 또는 phase/queryGroups를 필수로 받는다. client가 반환한
record는 저장 전에 이 identity와 exact provider/purpose가 같은지 runtime에서
검사한다.

### 7.6 YouTube 독립 수집

무작위 최근순은 사용하지 않는다. 다음 lane을 각각 호출한 뒤 합친다.

| lane | 기간 | 정렬 | 목적 |
|---|---:|---|---|
| recent-popular | 최근 7일 | viewCount | 짧은 기간의 인기 영상 |
| current-popular | 최근 30일 | viewCount | 현재 주제의 대표 인기 영상 |
| current-relevant | 최근 14일 | relevance | 검색어와 밀접한 영상 |

`search.list`의 각 lane, `videos.list`의 각 1~50 ID batch,
`commentThreads.list`의 각 단일 video는 서로 다른 source port 호출이며 호출마다
`researchRunId`, `asOf`, `attempt`, `signal`과 lane/query/batch/video identity를
명시한다. 여러 HTTP 호출을 하나의 aggregate adapter 메서드로 숨기지 않는다.
현재 범위의 search/comments는 호출별 첫 page 한 번만 수집한다. provider
`nextPageToken`은 evidence용 parsed output의 `pageCursor`로 이름을 바꿔 보존할 수
있지만 source port input이나 A3 request DTO에 넣지 않고 follow-up pagination 호출에
사용하지 않는다.

`search.list` 결과는 `videos.list`로 확장해 다음을 계산한다.

- 게시 시각
- 길이
- 조회수
- 좋아요·댓글 수
- 게시 후 시간당 조회수
- 검색 결과 집합 안의 상대 백분위
- 채널별 결과 개수

기본 필터:

- 주제 관련성 미달 제거
- 동일·유사 업로드 제거
- 한 채널이 결과를 독점하지 않도록 채널별 상한 적용
- 단순 누적 조회수가 아니라 시간당 조회수와 반응을 함께 사용
- 형식 분석 대상은 통과 결과 중 20~30개로 제한

공개 YouTube URL의 내용·형식 분석은 `gemini-3.6-flash`를 초기 모델로 사용한다.
분석 결과는 다음과 같이 구조화한다.

- 첫 훅의 형태와 시작 시각
- 전개 단계
- 장면 변화
- 자막·화면 문구 패턴
- 비교·설명·시연 방식
- 댓글에서 반복되는 질문·오해
- 관찰 한계와 confidence

YouTube 영상은 주제 발견과 Reference 입력에 모두 사용할 수 있다.

### 7.7 공식 자료 자동 탐색

조사 중 발견한 인물·브랜드·제품·기관·사건마다 다음 종류의 검색어를 추가한다.

- 공식
- 공식 발표
- 보도자료
- 출시
- 소속사·기관 공지
- 확인하려는 주장 키워드

출처 역할:

| 역할 | 사용 |
|---|---|
| official/primary | 날짜·제품·수치·발언 등 사실 확인 |
| authoritative secondary | 공식 자료가 없을 때 교차 확인 |
| market observation | 현재 어떤 주제·형식이 보이는지 |
| audience signal | 질문·오해·반응 |
| reference pattern | 훅·구조·시각 표현 |

사용자 첨부는 사내 자료·미공개 자료·반드시 사용해야 할 특정 링크가 있을 때만
`UserPinnedSource`로 추가한다.

### 7.8 최신성 판정

오래된 누적 인기 자료가 현재 트렌드로 오인되지 않게 한다.

- 모든 원본에 `publishedAt`, `collectedAt`, `asOf`를 기록한다.
- `asOf`는 research run 시작 때 한 번 동결한 UTC 시각이고 같은 run의 모든 source와
  상대 시각 파싱에 동일하게 사용한다. `collectedAt`은 해당 source 호출이 실제로
  완료되거나 실패한 UTC 시각이다.
- 현재 주제 점수에는 최근 기간 신호만 사용한다.
- 오래된 자료는 사실 배경이나 Reference로만 사용할 수 있다.
- `왜 지금인가`를 표시하려면 최근 자료 또는 시계열 변화가 필요하다.
- 검색 관심도 변화, 시간당 조회수, 최근 뉴스, 출처 다양성을 별도 값으로 보존한다.
- 단일 합산 점수만 저장하지 않고 구성 요소를 함께 저장한다.

지속 수집 이력이 없어도 실행 시점에 최근 기간과 직전 기간을 함께 조회해 변화량을
계산한다.

## 8. 증거 정규화와 주제 생성

### 8.1 EvidenceItem

모든 출처는 공통 `EvidenceItem`으로 정규화한다.

```ts
interface EvidenceItemV1 {
  schemaVersion: 'shortform-director-evidence.v1';
  id: string;
  researchRunId: string;
  sourceFetchId: string;
  sourceType:
    | 'google-trends'
    | 'naver-news'
    | 'naver-web'
    | 'naver-blog'
    | 'naver-datalab'
    | 'youtube-video'
    | 'youtube-comment'
    | 'official-source'
    | 'user-source';
  role: 'fact' | 'market' | 'audience' | 'reference';
  title: string;
  url?: string;
  excerpt?: string;
  publishedAt?: string;
  collectedAt: string;
  freshness: {
    ageHours?: number;
    window: '4h' | '24h' | '48h' | '7d' | '14d' | '30d' | 'background';
  };
  metrics?: Record<string, number | string | boolean | null>;
  confidence: 'high' | 'medium' | 'low';
  rightsRole: 'analysis-only' | 'production-eligible' | 'unknown';
}
```

### 8.2 Topic

주제는 영상 한 편이 아니다. 여러 영상 후보를 만들 수 있는 조사 결과 단위다.

```ts
interface ResearchTopicV1 {
  schemaVersion: 'shortform-director-topic.v1';
  id: string;
  researchRunId: string;
  title: string;
  summary: string;
  whyNow: string;
  evidenceIds: string[];
  sourceBreakdown: Record<string, number>;
  audienceQuestionIds: string[];
  referencePatternIds: string[];
  freshnessSignals: string[];
  cautions: string[];
  generatedByCallId: string;
  validation: {
    passed: boolean;
    issues: string[];
  };
}
```

### 8.3 TopicValidator

다음을 검증한다.

- 최소 하나 이상의 실제 근거
- `왜 지금인가`와 최신 신호의 연결
- 공식 사실과 시장 관측의 혼동 금지
- 프로필 관련성
- 같은 주제의 중복
- 출처별 주장 가능 범위
- 근거 ID의 실제 존재

검증 실패 주제와 실패 사유도 삭제하지 않고 저장한다.

## 9. 영상 후보 생성

사용자가 한 주제를 선택해 `영상 후보 만들기`를 실행하면 `CandidateGenerationRun`을
새로 만든다.

### 9.1 입력

- 프로필 snapshot
- 선택 Topic
- Topic의 EvidenceItem
- Audience signal
- Reference pattern
- 금지사항
- 목표 길이

### 9.2 생성과 검증

1. 약 20개의 원본 후보를 구조화 JSON으로 생성한다.
2. 훅·약속·관점·전개가 겹치는 후보를 군집화한다.
3. 근거 없는 주장, 한 편에 과도한 내용, 프로필 불일치 후보를 탈락시킨다.
4. 통과 후보가 10개 미만이면 부족한 관점만 지정해 추가 생성한다.
5. 첫 결과는 최소 10개, 보통 10~15개를 제공한다.
6. `영상 후보 더 만들기`는 기존 후보 ID와 요약을 입력해 새로운 후보를 10개 단위로
   추가한다.

### 9.3 VideoCandidate

```ts
interface VideoCandidateV1 {
  schemaVersion: 'shortform-director-video-candidate.v1';
  id: string;
  candidateRunId: string;
  topicId: string;
  title: string;
  hook: string;
  promise: string;
  whyNow: string;
  outline: string[];
  format: string;
  targetDurationSeconds: number;
  evidenceIds: string[];
  audienceSignalIds: string[];
  referencePatternIds: string[];
  generatedByCallId: string;
  validation: {
    passed: boolean;
    uniqueness: number;
    issues: string[];
  };
}
```

영상 후보 전체에 상세 장면 계획을 만들지 않는다. 사용자가 후보 하나를 선택한 뒤에만
비용이 더 드는 상세 설계를 실행한다.

## 10. 선택 후보의 장면 설계

상세 장면은 고정 초 단위가 아니라 다음 변화 지점에서 나눈다.

- 전달하려는 의미가 바뀜
- 새로운 주장·근거가 등장함
- 시각적으로 다른 설명이 필요함
- 훅·설명·증명·결론의 기능이 바뀜

각 장면은 다음 계약을 가진다.

```ts
interface ScenePlanV1 {
  id: string;
  videoPlanId: string;
  purpose: string;
  narration: string;
  onScreenText: string[];
  claimIds: string[];
  evidenceIds: string[];
  audienceSignalIds: string[];
  durationSeconds: number;
  mediaDecisionId: string;
  transition: string;
  audioDirection?: string;
}
```

상세 계획의 입력은 프로필, 선택 후보, 근거 graph, 내레이션 단어 예산, Reference
패턴이다. 각 장면은 사용 근거가 없거나 순수 연출 장면임을 명시해야 한다.

## 11. 장면별 시각 표현

### 11.1 고정 공급 순서 금지

미디어 준비는 보유 파일→공식 자료→검색→AI 생성 같은 순차 fallback이 아니다.
`SceneMediaDirector`가 먼저 장면의 커뮤니케이션 목적과 사실성 위험을 판단하고
표현 종류를 고른다. `MediaFulfillment`는 선택된 종류만 준비한다.

```ts
type SceneMedium =
  | 'official-source'
  | 'licensed-real-media'
  | 'generated-image'
  | 'generated-video'
  | 'programmatic-diagram'
  | 'kinetic-typography'
  | 'mixed-composition';
```

### 11.2 선택 기준

| 장면 목적 | 기본 표현 |
|---|---|
| 실제 인물·제품·사건 | 공식 자료 또는 사용 가능한 실제 자료 |
| 기사·수치·발표 증명 | 출처 카드·데이터 시각화 |
| 순서·원리·차이 설명 | Motion Canvas 도식·비교 구성 |
| 핵심 문장·훅 | 타이포그래피·모션 그래픽 |
| 분위기·비유·상상 | 생성 이미지 또는 생성 영상 |
| 촬영하기 어려운 짧은 행동 | 생성 영상 |
| 여러 정보 비교 | 직접 설계한 혼합 레이아웃 |

실제 제품 사진을 확보하지 못했다고 사실처럼 보이는 가짜 제품 영상을 만들지 않는다.
선택 매체가 실패하면 의미상 안전한 다른 장면 표현으로 다시 설계하고 이유를 기록한다.

### 11.3 조사 참고 영상과 제작 소재

YouTube 영상은 주제·형식이 실제로 관찰됐다는 `EvidenceItem` 또는
`ReferencePattern`이 될 수 있다. 발견·분석했다는 사실만으로 최종 영상에 그 장면을
잘라 쓸 수 있는 권리가 생기지는 않는다.

- `evidenceRef`: 조사 근거
- `productionMediaRef`: 최종 결과물에 실제로 들어가는 파일

둘은 별도 계약이다. 명시적인 재사용 가능 조건이 확인된 자료만
`production-eligible`로 승격한다.

## 12. 초기 모델·공급자 구성

이 구성은 첫 구현값이며 실제 테스트 결과가 우선한다. 모델 ID는 역할별 설정으로
분리하고 모든 호출 기록에 정확한 모델 ID를 저장한다.

### 12.1 텍스트·멀티모달

| 역할 | 초기 모델 |
|---|---|
| 자료 추출·분류·정규화 보조 | `gpt-5.4-nano` |
| 주제 생성 | `gpt-5.6-luna` |
| 영상 후보 생성 | `gpt-5.6-luna` |
| 상세 장면 설계 | `gpt-5.6-luna` |
| 비용 비교군 | `gpt-5.4-mini` |
| 품질·멀티모달 비교군 | `gemini-3.6-flash` |
| YouTube 영상 이해 | `gemini-3.6-flash` |
| 개선 전 기준선 | 현재 `gpt-4.1` 결과 |

Claude 계열 모델은 현재 비교군에 포함하지 않는다.

### 12.2 이미지

| 역할 | 모델 |
|---|---|
| 일반 장면 | `gemini-3.1-flash-image` |
| 대표 이미지·복잡한 연출 비교 | `gemini-3-pro-image` |

도식·비교표·정확한 한국어 화면 문구는 이미지 모델이 아니라 Motion Canvas에서 만든다.

### 12.3 영상

| 역할 | 모델 |
|---|---|
| 새 기본 후보 | `gemini-omni-flash-preview` |
| 현재 기준선 | `veo-3.1-fast-generate-preview` |
| 대표 장면 품질 비교 | `veo-3.1-generate-preview` |

Omni는 Preview이므로 실제 A/B 결과 전까지 단일 기본값으로 확정하지 않는다. 생성 영상
안의 한국어 문구는 모델에 맡기지 않고 렌더 단계에서 올린다.

### 12.4 비교 기준

- 근거 정확성
- 후보 간 중복
- 한국어 자연스러움
- 훅·전개·장면 설계 품질
- 구조화 JSON 성공률
- 지연·실패율
- 입력·출력 토큰과 실제 비용
- 생성 이미지·영상의 지시 준수
- 피사체·제품·인물 일관성
- 세로 화면 구성
- 재생성·수정 횟수

실제 유료 공급자 비교 전에는 예상 호출량과 비용을 사용자에게 제시하고 승인을 받는다.

## 13. 로컬 JSON 영속성

### 13.1 SoT와 기존 데이터 보존

- 구조화 콘텐츠·실행 이력 SoT는 `clipper_nestjs`의 `CLIPPER_DATA_DIR`이다.
- 결제·이용권·공급자 credential은 기존 `clipper_web_api` 경계를 유지한다. 단, AI
  Director 실행은 결제 operation과 연결하지 않고 크레딧을 차감하지 않는다.
- 실행 기록에는 API key, Authorization header, session token을 저장하지 않는다.
- 현재 `shortform-director/projects.json`은 기존 프로젝트 호환을 위해 유지한다.
- 조사·후보·호출 이력을 거대한 `projects.json`에 합치지 않고 실행별 파일로 추가한다.
- 기존 프로젝트 데이터의 파괴적 마이그레이션은 1차 범위에 포함하지 않는다.

### 13.2 디렉토리

```text
CLIPPER_DATA_DIR/
└─ shortform-director/
   ├─ profiles/
   │  ├─ index.json
   │  └─ <profileId>.json
   ├─ research-runs/
   │  ├─ index.json
   │  └─ <researchRunId>/
   │     ├─ manifest.json
   │     ├─ profile-snapshot.json
   │     ├─ input.json
   │     ├─ query-plan.json
   │     ├─ source-fetches/
   │     │  └─ <sourceFetchId>.json
   │     ├─ normalized/
   │     │  ├─ evidence-items.json
   │     │  ├─ trend-signals.json
   │     │  ├─ audience-signals.json
   │     │  ├─ reference-patterns.json
   │     │  └─ rejected-items.json
   │     ├─ llm-calls/
   │     │  └─ <llmCallId>.json
   │     ├─ topics.json
   │     ├─ rejected-topics.json
   │     └─ research-snapshot.json
   ├─ candidate-runs/
   │  └─ <candidateRunId>/
   │     ├─ manifest.json
   │     ├─ input.json
   │     ├─ llm-calls/
   │     ├─ raw-candidates.json
   │     ├─ rejected-candidates.json
   │     └─ video-candidates.json
   └─ projects/
      └─ <projectId>/
         ├─ project.json
         ├─ candidate-selections/
         │  └─ <selectionId>.json
         ├─ video-plan-runs/
         │  └─ <videoPlanRunId>/
         │     ├─ manifest.json
         │     ├─ input.json
         │     ├─ llm-calls/
         │     ├─ video-plan.json
         │     └─ scene-media-decisions.json
         ├─ media-runs/
         │  └─ <mediaRunId>/
         │     ├─ manifest.json
         │     ├─ media-jobs/
         │     └─ narration/
         ├─ render-runs/
         └─ quality-report-runs/
```

`project.json`은 현재 선택된 실행 ID를 가리키는 작은 포인터 문서다. 실제 후보 선택,
영상 계획, 미디어 작업, 렌더, 품질 결과는 실행별 디렉토리에 남으므로 재생성해도 이전
결과를 덮어쓰지 않는다.

### 13.3 공통 실행 manifest

```ts
interface LocalRunManifestV1 {
  schemaVersion: 'shortform-director-run-manifest.v1';
  id: string;
  kind:
    | 'research'
    | 'candidate-generation'
    | 'video-plan'
    | 'media'
    | 'render'
    | 'quality-report';
  ownerSubjectId: string;
  profileId: string;
  projectId?: string;
  status: 'running' | 'partial' | 'succeeded' | 'failed' | 'cancelled';
  startedAt: string;
  finishedAt?: string;
  inputRefs: string[];
  outputRefs: string[];
  failureRefs: string[];
  childRunIds: string[];
}
```

### 13.4 SourceFetch 기록

각 network source 호출마다 별도 JSON을 만든다. 로컬 파일 parse나 수동 CSV parse를
network fetch로 꾸미지 않는다.

```ts
type SourceFetchStoredBodyChecksum = `sha256:${string}`;
type SourceFetchReceivedBodyChecksum = `sha256:${string}`;

type SourceResponseRedactionKind =
  | 'auth-scheme'
  | 'key-material'
  | 'sensitive-query';

interface SourceResponseRedactionSummaryV1 {
  kind: SourceResponseRedactionKind;
  count: number;
}

type SourceFetchHttpRequestV1 = {
  kind: 'http';
  method: string;
  canonicalUrl: string;
  query?: Record<string, unknown>;
  body?: unknown;
  redactedFields: string[];
};

type SourceFetchContentTypeFieldsV1 =
  | {
      contentTypeRaw: string;
      mediaType: string;
    }
  | {
      contentTypeRaw?: never;
      mediaType?: never;
    };

type SourceFetchReceivedMetadataV1 = SourceFetchContentTypeFieldsV1 & {
  status: number;
  bytesReceived: number;
};

type SourceFetchNoResponseV1 = {
  received: false;
  complete: false;
  bytesReceived: 0;
  status?: never;
  contentTypeRaw?: never;
  mediaType?: never;
  decoded?: never;
  redactionComplete?: never;
  bodyRetention?: never;
  receivedBodyChecksum?: never;
  rawBody?: never;
  rawBodyBase64?: never;
  storedBodyChecksum?: never;
  parsed?: never;
};

type SourceFetchIncompleteResponseV1 =
  SourceFetchReceivedMetadataV1 & {
    received: true;
    complete: false;
    decoded?: never;
    redactionComplete?: never;
    bodyRetention?: never;
    receivedBodyChecksum?: never;
    rawBody?: never;
    rawBodyBase64?: never;
    storedBodyChecksum?: never;
    parsed?: never;
  };

type SourceFetchRetainedUndecodableCompleteResponseV1 =
  SourceFetchReceivedMetadataV1 & {
    received: true;
    complete: true;
    decoded: false;
    redactionComplete?: never;
    bodyRetention: 'retained';
    receivedBodyChecksum?: never;
    rawBody?: never;
    rawBodyBase64: string;
    storedBodyChecksum: SourceFetchStoredBodyChecksum;
    parsed?: never;
  };

type SourceFetchWithheldUndecodableCompleteResponseV1 =
  SourceFetchReceivedMetadataV1 & {
    received: true;
    complete: true;
    decoded: false;
    redactionComplete?: never;
    bodyRetention: 'withheld';
    receivedBodyChecksum: SourceFetchReceivedBodyChecksum;
    rawBody?: never;
    rawBodyBase64?: never;
    storedBodyChecksum?: never;
    parsed?: never;
  };

type SourceFetchRedactionFailedResponseV1 =
  SourceFetchReceivedMetadataV1 & {
    received: true;
    complete: true;
    decoded: true;
    redactionComplete: false;
    bodyRetention?: never;
    receivedBodyChecksum?: never;
    rawBody?: never;
    rawBodyBase64?: never;
    storedBodyChecksum?: never;
    parsed?: never;
  };

type SourceFetchStoredDecodedCompleteResponseV1 =
  SourceFetchReceivedMetadataV1 & {
    received: true;
    complete: true;
    decoded: true;
    redactionComplete: true;
    bodyRetention?: never;
    receivedBodyChecksum?: never;
    rawBody: string;
    rawBodyBase64?: never;
    storedBodyChecksum: SourceFetchStoredBodyChecksum;
  };

type SourceFetchFailedStoredResponseV1 =
  SourceFetchStoredDecodedCompleteResponseV1 & {
    parsed?: never;
  };

type SourceFetchSucceededResponseV1 =
  SourceFetchStoredDecodedCompleteResponseV1 & {
    parsed: unknown;
  };

type SourceFetchFailedResponseV1 =
  | SourceFetchNoResponseV1
  | SourceFetchIncompleteResponseV1
  | SourceFetchRetainedUndecodableCompleteResponseV1
  | SourceFetchWithheldUndecodableCompleteResponseV1
  | SourceFetchRedactionFailedResponseV1
  | SourceFetchFailedStoredResponseV1;

type SourceFetchResponseV1 =
  | SourceFetchFailedResponseV1
  | SourceFetchSucceededResponseV1;

type SourceFetchErrorCategory =
  | 'cancelled'
  | 'timeout'
  | 'network'
  | 'redirect'
  | 'http'
  | 'content-type'
  | 'body-too-large'
  | 'decode'
  | 'parse'
  | 'validation'
  | 'provider';

interface SourceFetchRecordBaseV1 {
  schemaVersion: 'shortform-director-source-fetch.v1';
  id: string;
  researchRunId: string;
  provider: string;
  purpose: string;
  asOf: string;
  window?: string;
  responseRedactions: SourceResponseRedactionSummaryV1[];
  request: SourceFetchHttpRequestV1;
  attempt: number;
  latencyMs: number;
  collectedAt: string;
}

type SourceFetchRecordV1 =
  | (SourceFetchRecordBaseV1 & {
      status: 'succeeded';
      response: SourceFetchSucceededResponseV1;
      error?: never;
    })
  | (SourceFetchRecordBaseV1 & {
      status: 'failed';
      response: SourceFetchFailedResponseV1;
      error: {
        category: SourceFetchErrorCategory;
        message: string;
      };
    });
```

`parseSourceFetchRecordV1`은 exact-key와 다음 불변식을 fail closed로 검사한다.

- `asOf`는 run에서 동결한 UTC 시각이다. `window`는 provider가 기간 호출을 구분할 때
  top-level에 두므로 pre-response와 parse 실패에서도 직접 식별할 수 있다.
- `succeeded`는 `received:true`, `complete:true`, `decoded:true`,
  `redactionComplete:true`, 2xx safe-integer status, `parsed` 존재, `error` 부재인
  경우뿐이다. `failed`는 모든 response 형태에서 `parsed`를 금지하고 `error`를
  필수로 둔다.
- response의 status는 존재하면 `100..599` safe integer다. `bytesReceived`는 safe
  nonnegative integer이고, `received:false`는 `complete:false`,
  `bytesReceived:0`이며 status/content-type/body 필드를 갖지 않는다.
- `contentTypeRaw`은 수신 header 원문이고 `mediaType`은 parameter를 제거하고
  trim/lowercase한 비교값이다. header가 없으면 둘 다 없고, header가 있으면 둘 다
  있어야 한다.
- header 뒤 중단되거나 byte cap을 초과한 body는 `received:true`,
  `complete:false`, 실제 `bytesReceived`로 기록하고 decoded/raw/checksum/parsed를
  두지 않는다.
- 완전한 bytes는 fatal UTF-8 decoder로 검사한다. invalid UTF-8이면
  `received:true`, `complete:true`, `decoded:false`,
  `error.category:'decode'`다. credential-free Google Trends RSS만
  `bodyRetention:'retained'`, canonical padded RFC 4648 `rawBodyBase64`와 그 문자열을
  decode한 bytes의 `storedBodyChecksum`을 필수로 둔다. decode bytes 길이가
  `bytesReceived`와 같아야 하고 whitespace, noncanonical padding/alphabet,
  decode→re-encode 불일치는 거부한다.
- credentialed Naver/YouTube는 invalid UTF-8 bytes나 base64를 public/local JSON에
  보존하지 않는다. 대신 `bodyRetention:'withheld'`,
  `receivedBodyChecksum:'sha256:<64 lowercase hex>'`만 남기고 `rawBody`,
  `rawBodyBase64`, `storedBodyChecksum`, `parsed`, `redactionComplete`는 모두
  금지한다. 이 fingerprint는 완전 수신한 wire bytes 식별용이며 저장 body checksum이
  아니다.
- valid UTF-8 body는 별도 narrow deterministic response redactor가 decoded XML과
  parsed DTO를 모두 정제한 뒤에만 `redactionComplete:true`, `rawBody`,
  `storedBodyChecksum`을 가질 수 있다. redactor가 안전한 두 출력을 만들지 못하면
  `redactionComplete:false`, `error.category:'validation'`이고 unsafe
  raw/base64/checksum/parsed를 모두 생략한다.
- JSON media type의 valid UTF-8 text가 malformed이면 decode 사실을 잃지 않는다.
  safe redaction을 통과한 text를 `rawBody`로 보존하고 그 UTF-8
  `storedBodyChecksum`을 계산하되 `parsed` 없이 `error.category:'parse'`로 닫는다.
- `responseRedactions`는 `{kind,count}`의 중복 없는 비민감 요약이다. `kind`는
  `auth-scheme|key-material|sensitive-query`, `count`는 positive safe integer이고
  고정 kind 순서로 저장한다. 변환이 없거나 body가 없거나 redaction이 실패하면 빈
  배열이다.
- terminal non-redirect HTTP 응답은 status 또는 content-type이 실패여도 같은 전체
  deadline과 streaming byte cap 안에서 body 수신을 시도한다. 제한 안에서 완전히 받은
  실패 응답은 원문과 checksum을 보존하고, 중단·초과한 응답은 incomplete 형태만
  허용한다.
- decoded branch의 `storedBodyChecksum`은 deterministic redaction 뒤 실제 JSON에
  저장된 `rawBody`의 UTF-8 bytes를 해시한 `sha256:<64 lowercase hex>`다.
  retained Google `decoded:false` branch에서는 실제 저장된 canonical base64를
  decode한 bytes를 해시한다. withheld non-Google branch의
  `receivedBodyChecksum`은 저장 body가 없으므로 형식과 A3 전달 일치만 검증하며
  `storedBodyChecksum`으로 오인하지 않는다. B1 artifact descriptor의 `checksum`은
  `SourceFetchRecordV1` wrapper JSON 전체 직렬화 bytes checksum이므로 별개다.
- `attempt`는 1 이상의 안전한 정수, `latencyMs`는 전체 호출의 유한한 비음수,
  `collectedAt`은 실제 terminal UTC 시각이다.

generic runtime parser가 허용하는 failed category/response 조합은 다음과 같다.
Provider parser는 이 표를 넓히지 않고 자기 계약에 맞게 더 좁힐 수 있다.

| response 형태 | 허용 failed category |
|---|---|
| `received:false, complete:false` | `cancelled`, `timeout`, `network`, `redirect` |
| `received:true, complete:false` | `cancelled`, `timeout`, `network`, `redirect`, `body-too-large` |
| `received:true, complete:true, decoded:false, bodyRetention:'retained'` | `decode` |
| `received:true, complete:true, decoded:false, bodyRetention:'withheld'` | `decode` |
| `received:true, complete:true, decoded:true, redactionComplete:false` | `validation` |
| `received:true, complete:true, decoded:true, redactionComplete:true` | `redirect`, `http`, `content-type`, `parse`, `validation`, `provider` |

`canonicalUrl`, `query`, `body`는 공급자에게 보낸 의미를 재현할 수 있는 정리된
요청이되 API key, 서명, 인증 header, session token은 저장 전에 제거한다. 공급자
  응답은 decode 뒤 provider별 deterministic redactor를 거친 값만 보존한다. C1의
Google Trends redactor는 decoded XML을 항상 받고 parser가 DTO를 만들었으면 그 DTO도
함께 받아 auth-scheme, key material, credential-bearing URL userinfo/query value를
B1-compatible `[removed]` marker 또는 query pair 제거로 정제한다. 무해한 값은
byte/value 의미를 바꾸지 않는다. 저장할 XML 또는 존재하는 parsed DTO 어느 한쪽이라도
안전하게 정제하지 못하면 둘 다 저장하지 않는다.

B1의 공용 sensitive-string/authorization 판단은 별도 pure classifier가 소유한다.
persistence guard와 C1/C2 response redactor가 같은 inspect+redact 함수를 호출해
provider별 exception이나 bypass를 만들지 않는다. 이 classifier의 exact 상수와
predicate는 다음과 같다.

- header는
  `/["']?\bauthorization\b["']?[ \t]*(?::|=)[ \t]*["']?(bearer|basic)[ \t]+([^\s,;}"']+)/dgi`
  match를 captured value 길이와 무관하게 차단한다. 따라서 plain header,
  `"authorization":"Bearer x"`, `'authorization':'Basic ...'`,
  `authorization=Bearer x`와 closing brace가 빠진 malformed JSON text를 같은
  규칙으로 잡는다. replacement span은
  `match.indices[1][0]..match.indices[2][1]`이어서 key, `:`/`=`, surrounding quote를
  보존한다.
- standalone Bearer candidate는
  `/\bbearer[ \t]+([A-Za-z0-9._~+/-]+={0,2})(?=$|[^A-Za-z0-9._~+/=-])/gi`로
  잡고 다음 중 하나일 때만 차단한다: case-sensitive
  `{'ya29.':16,AIza:16,'sk-':16,ghp_:16,github_pat_:24}` prefix/전체 길이
  threshold, 정확히 3개의 `/^[A-Za-z0-9_-]+$/` JWT segment와 각 최소 길이
  `[8,8,16]`, trailing `=` 제거 길이 24 이상이면서 letter·digit·`[._~+/-]`를
  모두 포함, 또는 trailing `=` 제거 길이 32 이상이면서 lowercase·uppercase·digit을
  모두 포함. entropy 계산이나 임의 사전은 쓰지 않는다.
- standalone Basic candidate는
  `/\bbasic[ \t]+([A-Za-z0-9+/]+={0,2})(?=$|[^A-Za-z0-9+/=])/gi`로 잡는다.
  unpadded 길이 2 이상/modulo 4가 1 아님, padding 복원→decode→unpadded base64
  re-encode exact 일치, 모든 decoded byte가 `0x20..0x7e`, 첫 `:`가
  index `1..length-2`인 경우에만 차단한다.
- private-key PEM은 `5 * 1024 * 1024` UTF-8 bytes 이하 입력에서만 inspect한다.
  body wildcard regex는 쓰지 않는다. ASCII-uppercase shadow와 한 forward cursor의
  state machine이 `-----BEGIN ` / `-----END ` boundary를 찾고, 최대 64 code-unit
  label이 `/^(?:[A-Z0-9]+ )?PRIVATE KEY$/`인 경우만 추적한다. 같은 label의
  BEGIN+body+END 전체가 complete span이다. open 상태의 nested BEGIN, open이 없을 때
  END, 다른 label END, missing END는 실패다. marker부터 다음 CR/LF 또는 96 code
  units 전까지 `PRIVATE KEY`가 있지만 closing delimiter·label 문법/길이가 틀린
  boundary도 실패다. complete block은 span 전체를 `[removed]` 하나로 바꾸고 multiple
  block은 왼쪽→오른쪽으로 결정한 non-overlapping span을 역순 교체한다. invalid
  boundary가 하나라도 있으면 partial replacement 없이 whole inspection이 실패한다.
- HTTP(S) URL은 WHATWG `URL` parse 후 username/password가 있거나 nonempty query
  value의 normalized key가 `secret|password|credential|authorization|signature`를
  포함하거나 `token|apikey` suffix 또는 exact `key`이면 차단한다. key
  normalization은 NFKC→lowercase→`[^a-z0-9]` 제거다.
- 빈 값 아닌 exact `sensitiveValues`는 raw, `encodeURIComponent`, percent hex만
  lowercase로 바꾼 variant, `URLSearchParams([['v', value]])`의 value 부분 form
  variant와 그 lowercase-percent-hex variant를 길이와 관계없이 substring
  차단한다. 입력은 valid percent run만 decode하는 동일 변환을 최대 2회 거치며
  `+`는 임의로 space로 바꾸지 않는다.

shared inspection 결과는
`{redactionComplete:true,sensitive,kinds,redacted}` 또는
`{redactionComplete:false,sensitive:true,kinds,failure:
'input-too-large'|'private-key-boundary'}` exact union이다. PEM scan을 원문에서 먼저
완결해 complete span을 제거한 뒤 나머지 classifier span을 deterministic `[removed]`
또는 query-pair 제거로 바꾼다. failure에는 `redacted`가 없다. guard는 complete/
incomplete 원문을 모두 reject하고 redactor는 failure면 whole response를 withhold한다.
`kinds`는 known-sensitive-value, authorization, private-key, credential-url 고정
순서의 unique list다.
complete PEM을 제거한 결과를 다시 inspect해 non-sensitive complete일 때만
codec→registry로 보낸다. 실제 `Authorization: Bearer x`, JWT, opaque mixed token,
`Basic dXNlcjpwYXNz`, complete/incomplete PEM, credential URL을 차단하면서 정상 문구
`Bearer Stearns outlook`, `Basic skincare guide`는 byte/value 그대로 보존한다.

shared classifier refinement 외 forbidden DTO key 정책은 넓히지 않는다. JSON field는
`sourceText`, `rawBody`, `rawBodyBase64`, `responseRedactions`처럼 guard를 통과하는
이름만 사용하고 exact `raw`, `rawresponse`, `headers`,
secret/password/private-key 계열, credential/authorization 포함 key,
token/API-key suffix key를 만들지 않는다.

Google Trends RSS record는 `provider:'google-trends'`,
`purpose:'trending-rss'`, 필수 `window:GoogleTrendsWindow`로 generic record를
좁힌다. request는 `kind:'http'`, `method:'GET'`,
`canonicalUrl:'https://trends.google.com/trending/rss'`이고 exact query가
`{geo:'KR',hours:GOOGLE_TRENDS_HOURS[window]}`여야 한다. 성공 record의
`response.parsed.window/asOf`는 top-level `window/asOf`와 같아야 한다. 실패에는
parsed가 없어도 top-level `asOf/window`와 request query가 그대로 남는다.
Generic response parser는 retained/withheld `decoded:false` branch를 구조적으로
검사한다. Google refinement는 exact Google Trends RSS의 retained-base64 branch만
허용하고 withheld branch를 거부한다. non-Google refinement는 withheld-checksum
branch만 허용하고 retained/base64 branch를 거부한다. credentialed source가 base64로
B1 guard를 우회하지 못하게 한다.

Google Trends client는 RSS bytes 수신과 XML parse를 끝내고 위 Google Trends
refinement를 만족하는 `SourceFetchRecordV1`을 반환한다. C2는 각 record를 받는 즉시
immutable `source-fetch` JSON artifact로 저장하고, artifact registry에서 다시 읽어
`parseSourceFetchRecordV1`을 통과한 값만 정규화·LLM 입력에 사용한다. 메모리에 있던
client 반환값을 직접 downstream으로 넘기지 않는다. XML parser 실패 record도 valid
UTF-8의 완전 수신·redaction 뒤 원문과 stored-body checksum을 먼저 보존한다. CSV
parser 결과는 이 network record 흐름에 포함하지 않는다.

#### C2 non-Google B1-safe response refinement

A3 `ProviderCallAuditV1`은 web transport audit일 뿐 local artifact 계약이 아니다.
A3 response는 다음 exact discriminated union으로 실제 transport/decode/parse 상태를
표현한다.

```ts
type ProviderReceivedBodyChecksum = `sha256:${string}`;

type ProviderCallFailureKind =
  | 'cancelled'
  | 'provider_4xx'
  | 'provider_5xx'
  | 'timeout'
  | 'network_error'
  | 'response_too_large'
  | 'invalid_response';

type ProviderCallReceivedMetadataV1 = {
  received: true;
  status: number;
  contentType: string | null;
  bytesReceived: number;
};

type ProviderCallNoResponseV1 = {
  received: false;
  complete: false;
  bytesReceived: 0;
  status?: never;
  contentType?: never;
  decoded?: never;
  parseState?: never;
  redactionComplete?: never;
  bodyRetention?: never;
  receivedBodyChecksum?: never;
  raw?: never;
};

type ProviderCallIncompleteResponseV1 =
  ProviderCallReceivedMetadataV1 & {
    complete: false;
    decoded?: never;
    parseState?: never;
    redactionComplete?: never;
    bodyRetention?: never;
    receivedBodyChecksum?: never;
    raw?: never;
  };

type ProviderCallUndecodableResponseV1 =
  ProviderCallReceivedMetadataV1 & {
    complete: true;
    decoded: false;
    parseState?: never;
    redactionComplete?: never;
    bodyRetention: 'withheld';
    receivedBodyChecksum: ProviderReceivedBodyChecksum;
    raw?: never;
  };

type ProviderCallDecodedSafeTextResponseV1 =
  ProviderCallReceivedMetadataV1 & {
    complete: true;
    decoded: true;
    parseState: 'not-attempted' | 'failed';
    redactionComplete: true;
    bodyRetention?: never;
    receivedBodyChecksum?: never;
    raw: string;
  };

type ProviderCallParsedResponseV1 =
  ProviderCallReceivedMetadataV1 & {
    complete: true;
    decoded: true;
    parseState: 'parsed';
    redactionComplete: true;
    bodyRetention?: never;
    receivedBodyChecksum?: never;
    raw: unknown;
  };

type ProviderCallDecodedRedactionFailedResponseV1 =
  ProviderCallReceivedMetadataV1 & {
    complete: true;
    decoded: true;
    parseState: 'not-attempted' | 'failed' | 'parsed';
    redactionComplete: false;
    bodyRetention: 'withheld';
    receivedBodyChecksum?: never;
    raw?: never;
  };

type ProviderCallAuditResponseV1 =
  | ProviderCallNoResponseV1
  | ProviderCallIncompleteResponseV1
  | ProviderCallUndecodableResponseV1
  | ProviderCallDecodedSafeTextResponseV1
  | ProviderCallParsedResponseV1
  | ProviderCallDecodedRedactionFailedResponseV1;
```

header를 받기 전 network/timeout/caller abort는 no-response라서 status/content/body
metadata를 합성하지 않는다. header 뒤 timeout/abort/stream error/oversize는 actual
accumulated `bytesReceived`와 `complete:false`를 남긴다. `contentType`은 header가
없을 수 있어 `null`이지만 received branch의 `status`는 필수다.

완전 수신 bytes는 `TextDecoder('utf-8', {fatal:true})`로 decode한다. invalid UTF-8은
`complete:true`, `decoded:false`, raw/base64 없음,
`receivedBodyChecksum`만 가진다. provider credential이 echo됐을 가능성이 있는 bytes나
base64를 web audit 또는 local artifact에 넣지 않는다. valid UTF-8 JSON parse 실패는
`decoded:true`, `parseState:'failed'`이며 audit redactor를 통과한 원문 text를
`raw`로 보존한다. parsed JSON은 `parseState:'parsed'`, non-JSON text는
`parseState:'not-attempted'`다. audit redactor가 안전한 값을 만들지 못하면 decode/parse
사실은 보존하되 `redactionComplete:false`, `bodyRetention:'withheld'`, raw 없음으로
닫고 fixed `invalid_response` failure를 반환한다.

web A3 redactor는 package 경계 때문에 desktop classifier file을 import하지 않지만
5 MiB/64-label/96-lookahead PEM constants, linear boundary state machine,
redaction-complete union과 complete/incomplete fixture table을 exact mirror한다.
complete block은 full span을 제거하고 any invalid boundary는 raw 전체를 withhold한다.

C2가 wire state를 canonical body 길이에서 합성하지 않도록 desktop transport는 위
union을 exact parse한다. A3 `parseState`는 local response shape가 아니라
transport-only branch selector다. local `SourceFetchRecordV1` 어느 interface에도
없고 local runtime parser는 이 key를 reject한다. mapper는 다음 priority의 첫 match로
local branch를 선택한 뒤 `parseState`를 소거한다.

| priority | A3 조건 | exact local 결과 |
|---:|---|---|
| 1 | no-response | status/content/body 없음; A3 cancelled/timeout/network_error를 local cancelled/timeout/network로 변환 |
| 2 | received-incomplete | 같은 status/content/actual bytes; response_too_large만 body-too-large, 나머지는 위 failure mapping |
| 3 | complete undecodable | 같은 status/content/bytes/checksum의 withheld decode failure |
| 4 | A3 redactor 또는 필요한 local projector의 decoded redaction incomplete | status보다 먼저 body/checksum/parsed 없는 validation failure |
| 5 | decoded complete status `100..199`/`300..399` | terminal source result로 금지된 status라 body/checksum/parsed 없는 validation failure |
| 6 | decoded complete status `400..599` | parse state와 무관한 http failure; safe text 또는 failure evidence canonical rawBody+stored checksum, parsed 없음 |
| 7 | 2xx parse failed | safe text rawBody+checksum, parsed 없는 parse failure |
| 8 | 2xx expected JSON인데 parse not-attempted | safe text rawBody+checksum, content-type failure |
| 9 | 2xx parsed known Naver/YouTube error | failure evidence rawBody+checksum, parsed 없는 provider failure |
| 10 | 2xx parsed exact success DTO | same projected DTO의 rawBody/parsed+checksum success |
| 11 | 2xx parsed unknown/schema mismatch | body/checksum/parsed 없는 validation failure |

priority 6은 Naver/YouTube 모두 local `http` 하나이고 local `provider`는 priority 9에만
쓴다. A3 failure rename은
`cancelled→cancelled`, `timeout→timeout`, `network_error→network`,
`response_too_large→body-too-large`만 허용한다. 해당 local branch가 가진 `status`,
wire `bytesReceived`, `complete`, `decoded`만 보존한다. `contentType`은
`contentTypeRaw/mediaType` 쌍으로 정규화하고 canonical body 길이로 wire bytes를
만들지 않는다. branch 선택이 끝나면 `parseState`를 폐기하며 local artifact
schema에는 이 field가 없다.

desktop adapter는 `providerCredentialId`, `response.raw`를 포함한 A3 wrapper나
arbitrary provider payload object를 B1 registry에 직접 넘기지 않는다.

complete parsed 4xx/5xx는 success DTO mapper와 분리한 failure-body projector가
처리한다. known Naver envelope는 own string `errorCode/errorMessage`를
`code/summary`로, known YouTube envelope는 own plain `error`의 bounded
`code/status/message/errors[].domain/reason/message`를
`httpCode/statusText/summary/reasons`로 allowlist projection한다. known envelope의
extension/malformed/limit-excess field는 subtree당 `omittedEntries` 1이며 shared
classifier redaction과 code/status/reason/domain 128, summary 2,048 code-point
truncation을 `redactedValues/truncatedValues`로 센다.

drop/projection 전에는 A3 4 MiB cap 아래 parsed tree 전체를 iterative own-data
preflight한다. accessor/inherited/symbol/cycle/non-JSON value와 depth 32 초과를
reject하고 allowlist 밖 subtree까지 every string key/value의 PEM boundary를 scan한다.
complete block은 보존 field에서 full-span 제거하고 incomplete boundary 하나라도
있으면 whole projection failure다.

4xx/5xx unknown parsed JSON은 exact tagged tree로 보존한다. scalar는
`{kind:'null'|'boolean'|'number'|'text',value?}`, array는
`{kind:'list',items}`, object는 `{kind:'map',entries:[{name,value}]}`다. provider
object key는 JSON key가 아니라 `name` string만 된다. root depth 0/max depth 6,
node+entry 48, container 16, name 64 code points, text 160 code points, canonical
UTF-8 64 KiB다. object key를 UTF-16 ascending으로 방문하고 excess subtree는 내부를
세지 않고 omitted 1, truncated string은 `…[truncated]` suffix를 포함한다. normalized
name이 exact raw/rawresponse/header/cookie/cause/stack/config 계열,
secret/password/privatekey/credential/authorization/signature 포함, 또는 token/apikey
suffix면 entry 전체를 drop한다. 나머지 key/value string은 shared classifier를
통과한다. complete PEM은 full block replacement, incomplete PEM·non-JSON own-data
violation·canonical cap failure는 whole projection failure다.

failure evidence DTO는 exact
`shortform-director-naver-provider-failure.v1`/`naver-provider-failure`,
`shortform-director-youtube-provider-failure.v1`/`youtube-provider-failure`,
`shortform-director-generic-provider-failure.v1`/`generic-provider-failure`
schema/source pair와 `omittedEntries/redactedValues/truncatedValues`를 가진다. Naver
필드는 `code/summary`, YouTube는 optional `httpCode/statusText`,
`summary/reasons`, generic은 `provider/root`다. exact runtime parser를 통과한 뒤
canonical serializer가 scalar에 `JSON.stringify`, array 원래 순서, object own key
UTF-16 ascending, whitespace 없음 규칙을 재귀 적용한다. `rawBody`는 이
post-redaction evidence JSON, checksum은 그 UTF-8 bytes이고 local `parsed`는 항상
없다. status 2xx에는 known error projector만 허용하고 unknown generic fallback은
validation-withheld다. A3 wrapper/raw object 자체를 stringify하지 않는다.

non-Google success의 `parsed`는 다음 exact DTO 중 하나다. 표에 없는 top-level/item
key와 arbitrary nested object는 runtime refinement가 거부한다.

| DTO / schemaVersion | exact top-level | exact nested item |
|---|---|---|
| `NaverNewsParsedV1` / `shortform-director-naver-news.v1` | `schemaVersion`, `source:'naver-news'`, `page`, `items` | `title`, `url`, optional `sourceUrl`, `summary`, `publishedAtSourceText`, optional `publishedAt` |
| `NaverWebParsedV1` / `shortform-director-naver-web.v1` | `schemaVersion`, `source:'naver-web'`, `page`, `items` | `title`, `url`, `summary` |
| `NaverBlogParsedV1` / `shortform-director-naver-blog.v1` | `schemaVersion`, `source:'naver-blog'`, `page`, `items` | `title`, `url`, `summary`, `authorName`, optional `authorUrl`, `publishedAtSourceText`, optional `publishedAt` |
| `NaverDataLabParsedV1` / `shortform-director-naver-datalab.v1` | `schemaVersion`, `source:'naver-datalab'`, `phase`, `startDate`, `endDate`, `timeUnit:'date'`, `series` | series는 `title`, `terms`, `points`; point는 `period`, `ratio` |
| `YouTubeSearchParsedV1` / `shortform-director-youtube-search.v1` | `schemaVersion`, `source:'youtube-search'`, `lane`, optional `pageCursor`, `totalResults`, `resultCount`, `items` | `videoId`, `publishedAt`, `channelId`, `title`, `description`, optional `thumbnailUrl` |
| `YouTubeVideosParsedV1` / `shortform-director-youtube-videos.v1` | `schemaVersion`, `source:'youtube-videos'`, `lane`, `items` | `videoId`, `publishedAt`, `channelId`, `channelTitle`, `title`, `description`, optional `thumbnailUrl`, `durationSeconds`, `viewCount`, optional `likeCount/commentCount` |
| `YouTubeCommentsParsedV1` / `shortform-director-youtube-comments.v1` | `schemaVersion`, `source:'youtube-comments'`, `videoId`, optional `pageCursor`, `items` | `threadId`, `commentId`, `authorName`, `text`, `publishedAt`, `updatedAt`, `likeCount`, `replyCount` |

Naver `page`는 exact `start/returned/total` nonnegative safe integer다. 모든 배열/string은
bounded이고 count/duration은 safe nonnegative integer, ratio는 finite nonnegative
number, date/UTC/URL은 field별 형식 validator를 통과해야 한다. runtime
`parseNonGoogleSourceFetchRecordV1`은 generic parser 뒤 source DTO뿐 아니라
provider/purpose/request를 함께 좁힌다. DataLab purpose와 `phase`, YouTube purpose
suffix와 `lane`, comments request와 `videoId`가 같아야 한다.

failed refinement는 `provider`가 2xx known failure evidence에만, `http`이 4xx/5xx에만
쓰였는지 검사한다. recognized failure-evidence JSON rawBody는 exact parser, canonical
re-stringify와 checksum을 통과해야 하고 나머지 redacted text/HTML/malformed JSON은
string evidence다. 모든 failed branch에는 parsed가 없고 decode/validation withheld
branch에는 body/checksum도 없다. local response의 `parseState` key는 항상 거부한다.

success provider audit mapper는 arbitrary key를 재귀 복사하지 않는 allowlist
projection이다. parsed 2xx raw object 자체는 저장하지 않고 projected DTO에서만
canonical `rawBody`와 same `parsed`를 만든다. YouTube `nextPageToken`은
`pageCursor`, Naver `originallink`는 `sourceUrl`,
`bloggername/bloggerlink`는 `authorName/authorUrl`,
`pageInfo.resultsPerPage`는 `resultCount`로 바꾼다. `providerCredentialId`,
provider `accessToken`, 그 밖의 extension key는 저장하지 않는다.
`pageCursor`는 provider가 첫 page 응답에서 보낸 다음-page 근거를 표시하기 위한 output
필드일 뿐이다. 현재 C2의 YouTube search/comments input과 A3 DTO에는 cursor를
추가하지 않으며 후속 page를 호출하지 않는다.

success mapper도 allowlist projection 전에 같은 iterative own-data/PEM preflight를
raw tree 전체에 적용해 dropped extension 안 incomplete boundary도
validation-withheld로 닫는다.

projected success DTO는 별도 narrow deterministic redactor를 한 번 통과한다. auth
scheme, complete PEM, credential-bearing URL만 B1-compatible marker/query removal로
정제하고 fixed-order `responseRedactions`를 만든다. incomplete PEM이면 whole
response를 withhold한다. 정제 DTO에서 canonical `rawBody`와 `parsed`를 함께
파생하므로 `JSON.parse(rawBody)`와 parsed가 exact deep-equal이고 checksum은
post-redaction rawBody UTF-8 bytes로 재계산 가능해야 한다. 한 logical field를
body/parsed 복제 때문에 두 번 세지 않는다. safe pair를 만들지 못하면
`redactionComplete:false`, validation failed record로 닫고 unsafe
rawBody/checksum/parsed를 모두 생략한다.

구현 책임은 transport adapter, source별 success audit mapper, failure-body
projector, response redactor, domain runtime refinement로 분리한다. 각 Naver
news/web/blog/DataLab과 YouTube
search/videos/comments method는 actual B1 codec→registry publish→reload integration
test를 가진다. provider-specific guard/redactor exception은 없고 C1/C2 redactor와
persistence guard가 같은 shared sensitive-string classifier를 사용한다.
`ShortformDirectorSourceFetchArtifactValidator`도 registry encode 경계에서
provider/purpose를 읽어 exact Google refinement 또는 non-Google refinement로
dispatch한다. producer validation을 우회한 forged generic success와 wrong
schema/lane/phase/videoId도 publication 전에 거부한다.

#### C2 source-call identity와 pipeline failure

모든 network source client의 예상 가능한 network/HTTP/content/parser/provider
실패는 rejected promise가 아니라 strict failed `SourceFetchRecordV1`이다. 반대로
unexpected client throw, 반환 record runtime parse 실패, 반환 identity 불일치,
artifact publish 또는 reload rejection은 ordinary source partial이 아니라 source
collection/persistence pipeline failure다.

```ts
interface ResearchSourceCallContextV1 {
  researchRunId: string;
  asOf: string;
  attempt: number;
  signal: AbortSignal;
}

type ResearchPipelineFailureStage =
  | 'source-client'
  | 'record-validation'
  | 'artifact-publish'
  | 'artifact-reload';

interface ResearchPipelineFailureV1 {
  schemaVersion: 'shortform-director-research-pipeline-failure.v1';
  id: string;
  runId: string;
  code: 'source_collection_pipeline_failed';
  category: 'infrastructure';
  stage: ResearchPipelineFailureStage;
  message: 'The research source collection could not be persisted safely.';
  detectedAt: string;
}
```

artifact kind는 exact `research-pipeline-failure`이고
`parseResearchPipelineFailureV1`이 exact keys, local run ID,
`failure.director.<32 lowercase hex>` ID, UTC `detectedAt`, 고정
code/category/message와 stage enum을 검사한다. 이 parser를 소유한 public artifact
validator는 기존 `run-failure`와 `source-fetch` validator 목록에 append한다.

coordinator는 각 반환 record의 `researchRunId/asOf/attempt/provider/purpose/window`
identity를 호출 input과 runtime 비교한다. required query/lane/phase/batch/video
input과 실제 provider request 일치는 adapter contract test가 검증한다. 일치한
success/failed record를 각각 즉시 publish하고 registry에서 reload한 뒤 다시
parse·identity 검사한다. reload된 succeeded record만 다음 batch 계산, ranking,
normalizer와 LLM 입력에 쓰며 fulfilled failed record는 failure collection과 최종
상태 계산에만 쓴다.

첫 pipeline rejection은 injected wall clock으로 `stage/detectedAt`만 latch하고
run-level controller를 abort한다. exact-key parser와 public artifact validator를
통과한 위 고정 artifact를 실제 B1
`publishAndTransitionFailure(..., status:'failed')`로 publish·전환한다. rejection의
원문 reason/stack은 artifact나 logger에 복사하지 않는다.

B1의 failure publication은 immutable artifact publish→manifest replace→mutable
run-index replace 순서이며 하나의 원자 transaction이 아니다. 따라서 publisher I/O
rejection 직후 status를 `running` 또는 `failed`로 단정하지 않는다.

| fault 지점 | 가능한 durable state | reconcile/recovery 결과 |
|---|---|---|
| artifact publish rejection | manifest/run index는 transition 전 상태다. payload-only orphan, 또는 payload+descriptor가 durable하지만 artifact index만 stale일 수 있다. | artifact index가 durable descriptor+payload만 복원하고 payload-only orphan은 공개하지 않는다. 이어 run index를 reconcile한 뒤 durable manifest가 `running`일 때만 `process_interrupted` recovery를 수행한다. |
| artifact 성공 뒤 manifest replace rejection | failure artifact는 durable하다. rename/file sync 경계상 manifest는 이전 `running`, requested `failed`, 또는 외부 winner의 terminal일 수 있고 run index는 stale할 수 있다. | 두 index를 먼저 reconcile한다. durable manifest가 `running`일 때만 기존 recovery marker를 재사용하거나 새 `process_interrupted`를 만든다. terminal이면 그대로 보존한다. |
| manifest `failed` replace 성공 뒤 run-index replace rejection | manifest는 requested `failed`와 failure ref를 가지지만 index는 stale `running`일 수 있다. | run-index reconciliation이 manifest SoT에서 `failed` projection을 재생성한다. recovery running 목록에서 제외하므로 `process_interrupted`를 추가하지 않는다. |
| `transitionRunning() === null` | cancel/failure/success 중 다른 terminal transition이 먼저 이겼다. 새 failure artifact는 durable orphan일 수 있다. | publisher는 fixed `ShortformDirectorRunTerminalTransitionConflictError`로 reject하고 coordinator는 실제 terminal manifest를 reload해 winner를 보존한다. requested failure가 이겼다고 보고하지 않는다. |

현재 B1 publisher가 nullable transition 결과를 무시하는 seam은 C2에서 최소 수정한다.
resolved `publishAndTransitionFailure`만 requested `failed` manifest와 failure ref가
durable하다는 뜻이다. C2는 위 typed terminal conflict만 manifest reload로 해소하고
다른 I/O rejection은 outer coordinator로 전파한다.

owner/run별 단일 coordinator lease가 source wave 중복 실행을 막는다. cancel은 active
controller를 abort한 뒤 같은 compare-and-transition 경계에 합류한다. profile archive가
snapshot admission 전에 이기면 start는 stable 409이고, snapshot capture 뒤에 이기면
이미 동결된 run을 바꾸지 않는다. cancel이나 외부 success/failure transition이 먼저
terminal을 만들면 C2는 reload한 durable winner를 그대로 반환한다.

coordinator는 같은 owner/run keyed terminalization lock 아래 공통
`abortOrTerminalGate`를 사용한다. DELETE cancel은 먼저 internal abort intent를
`cancel`로 latch하고 active controller를 즉시 abort한 뒤 이 lock에 합류한다. gate는
signal과 durable manifest를 함께 reload해 다음처럼 동작한다.

abort intent는 `active→cancel|pipeline-failure` first-writer-wins latch다. cancel이 먼저
이면 뒤 unexpected rejection이 pipeline failure로 승격하지 않고 cancel을 보존한다.
pipeline failure가 먼저면 뒤 DELETE는 intent를 덮지 않고 failure publication 경계가
terminalize하도록 기다린 뒤 actual manifest를 반환한다. 이미 latched cancel 요청은
idempotent하다.

- manifest가 이미 terminal이면 그 winner를 반환하고 이후 LLM 호출, output/failure
  attach, final transition을 시작하지 않는다.
- manifest가 `running`이고 cancel intent의 signal이 aborted면 같은 lock 안에서
  `cancelled` transition을 시도하고 nullable 결과는 actual terminal manifest reload로
  해소한다.
- pipeline-failure intent로 abort된 signal은 cancel로 바꾸지 않고 failure publication
  경계로 전달한다.
- manifest가 `running`이고 signal도 active일 때만 다음 작업을 허용한다.

source artifact와 inference output publication은
`withRunningPublicationGate`가 gate 확인부터 `publishAndAttachJson` admission까지 같은
terminalization lock에 묶는다. 이 lock의 publication admission과 DELETE terminal
transition 중 먼저 잡힌 쪽이 선형화된다. durable terminal 뒤에는 새 attach가 없다.

gate는 각 source fetch admission과 wave 직후, synchronous
parse/rank/normalize/validate stage를 같은 terminalization lock으로 감싼 경계,
query-plan/source-normalization/YouTube-reference-analysis/topic-synthesis inference
직전과 직후, 모든 artifact publication 직전, final terminal transition 직전에
적용한다. 네 inference port input은 모두 필수 `AbortSignal`을 받으며 desktop
transport가 그 signal을 actual HTTP 요청에 전달한다. pre-call gate 직후 cancel
race는 transport abort가 중단하고, provider가 거의 동시에 반환해도 post-call gate가
output publication을 차단한다.

### 13.5 LLM 호출 기록

```ts
interface LlmCallRecordV1 {
  schemaVersion: 'shortform-director-llm-call.v1';
  id: string;
  parentRunId: string;
  purpose: string;
  provider: 'openai' | 'google';
  model: string;
  promptTemplateVersion: string;
  request: {
    systemPrompt?: string;
    userPrompt: string;
    responseSchema?: object;
    options?: Record<string, unknown>;
  };
  response?: {
    providerRequestId?: string;
    raw: unknown;
    text?: string;
    parsed?: unknown;
  };
  validation?: {
    passed: boolean;
    issues: string[];
  };
  usage?: {
    inputTokens?: number;
    outputTokens?: number;
    reasoningTokens?: number;
    estimatedCostUsd?: number;
  };
  attempt: number;
  latencyMs: number;
  status: 'succeeded' | 'failed';
  error?: {
    category: string;
    message: string;
  };
  createdAt: string;
}
```

저장 대상:

- 실제 조립된 prompt
- response schema와 모델 옵션
- 공급자가 반환한 공개 응답
- 파싱 결과
- 검증·탈락 이유
- 토큰 사용량·예상 비용·지연
- 실패·재시도

저장하지 않는 대상:

- credential과 인증 header
- 공급자가 반환하지 않는 내부 추론
- 복구할 수 없는 민감 signed query

### 13.6 미디어 파일

조사·호출·판정과 모든 구조화 metadata는 JSON이다. PNG·MP4·WAV 같은 바이너리를
base64 JSON으로 중복 저장하지 않는다. 바이너리는 기존 로컬 파일 저장소에 두고 다음
sidecar JSON을 둔다.

- 파일 경로
- MIME
- 바이트 크기
- SHA-256
- 생성·수집 공급자
- 입력 prompt 또는 source reference
- 사용 조건
- 연결된 scene ID

### 13.7 불변 실행과 원자 저장

- 원본 SourceFetch와 LlmCall은 생성 후 덮어쓰지 않는다.
- 재시도는 같은 파일 수정이 아니라 새 attempt record로 남긴다.
- 재조사·재생성은 새 run ID를 만든다.
- 실행 디렉토리와 최초 `manifest.json`을 먼저 만들어 진행 상태를 노출한다.
- manifest, index, 현재 실행 포인터처럼 바뀔 수 있는 JSON은 같은 디렉토리의 임시
  파일에 완전히 쓴 뒤 파일 단위 rename으로 교체한다.
- SourceFetch, LlmCall, 동결 snapshot 같은 불변 산출물은 같은 디렉토리의 temp에
  완전히 쓰고 file sync한 뒤 hard-link no-replace로 최종 경로에 한 번만 공개한다.
  같은 ID가 이미 있으면 byte가 같아도 덮어쓰기 성공으로 처리하지 않는다.
- 외부에 한 덩어리로 보여야 하는 render input 묶음은 현재 구현처럼 임시 디렉토리를
  완성한 뒤 디렉토리 단위 rename을 사용한다.
- 진행 중 실행은 manifest의 `running`으로 보이고, 일부 출처 실패 뒤 결과가 남은
  `partial`은 `finishedAt`을 가진 terminal 상태다. startup recovery는 `running`만
  `failed` + `process_interrupted` failure record로 전환한다. startup은 artifact
  index와 run index를 먼저 reconcile하므로 stale `running` index가 아니라 durable
  manifest 상태를 기준으로 판단한다.
- mutable index는 목록 탐색용이며 실제 실행 detail의 SoT가 아니다.

## 14. 데이터 계보

모든 결과는 상위 입력을 ID로 참조한다.

```text
profileId
  ↓
researchRunId
  ↓
sourceFetchId
  ↓
evidenceId / audienceSignalId / referencePatternId
  ↓
topicId
  ↓
candidateRunId → videoCandidateId
  ↓
videoPlanId → sceneId
  ↓
mediaDecisionId → mediaJobId
  ↓
renderRunId → output
```

각 단계는 `generatedByCallId`, `derivedFrom`, `evidenceIds` 중 해당 필드를 가진다.
UI의 lineage 조회는 텍스트 검색으로 JSON을 전부 훑지 않고 repository가 이 ID를
해결해 반환한다.

## 15. `근거·과정` UX

### 15.1 노출 방식

모든 상세를 기본 카드에 넣지 않는다.

- 각 결과에는 `근거·과정` 버튼과 요약 count를 둔다.
- 버튼은 오른쪽 상세 패널을 연다.
- 전체 원본 탐색은 별도 `실행 기록` 페이지에서 제공한다.

예:

```text
[근거·과정]  출처 14 · AI 호출 3
```

tooltip:

```text
이 결과가 만들어진 자료와 처리 과정을 확인합니다.
```

### 15.2 패널 탭

| 탭 | 내용 |
|---|---|
| `요약` | 왜 이 결과가 나왔는지 쉬운 설명 |
| `근거` | 뉴스·Trends·YouTube·공식 자료 |
| `처리 과정` | 검색어, 필터, 점수 구성, 탈락 이유 |
| `AI 호출` | 모델, prompt, response, token, 비용, 지연 |
| `원본 JSON` | 저장된 JSON 읽기·복사 |
| `파일 정보` | 로컬 상대 경로, checksum, 생성 시각 |

### 15.3 페이지별 연결

아이디어 찾기:

- 주제별 출처 구성
- 조사 기준 시각과 최신성
- `whyNow`의 근거
- 통과·주의 신호

영상 후보:

- 상위 topic
- 사용 Evidence·Audience·Reference
- 생성 모델과 prompt
- 중복 제거·검증 결과

영상 제작:

- 장면이 전달하는 claim
- 사용 evidence
- 해당 medium을 고른 이유
- 이미지·영상 prompt와 공급자 결과
- 파일 checksum

완성 영상:

- 전체 제작 기록
- 사용 모델·API·미디어
- 장면별 품질 검사
- 총 token·예상 공급자 비용·소요 시간

### 15.4 실행 기록 페이지

필터:

- 프로필
- 실행 종류
- 공급자
- 모델
- 상태
- 날짜

상세:

- 부모·자식 run
- 단계별 timeline
- 원본 request·response
- 오류와 재시도
- 산출 JSON
- 연결된 주제·후보·프로젝트·장면

결제 정보와 credential 관리 화면은 이 페이지에 합치지 않는다.

## 16. 로컬·웹 책임 경계

### 16.1 `clipper_nestjs`

- 전체 조사·생성 workflow 오케스트레이션
- 로컬 JSON repository
- 실행 manifest와 lineage 관리
- 정규화·검증·부분 실패 처리
- Angular용 raw 응답 API
- 기존 렌더·TTS·로컬 미디어 경로 연결

### 16.2 `clipper_web_api`

- 기존 신원·이용권·결제 SoT
- 기존 공급자 credential SoT
- credential이 필요한 외부 API·LLM·생성 모델 호출 경계
- desktop이 로컬에 기록할 수 있도록 모델·usage·provider request ID와 공개 응답 반환
- API key·Authorization header·결제 detail은 반환하지 않음

웹 API는 조사 콘텐츠의 장기 SoT가 아니다. 호출 결과를 받은 desktop이 로컬 JSON으로
영속한다.

### 16.3 `clipper_angular`

- 플러그인 내부 서브 페이지와 사용자 흐름
- 결과별 `근거·과정` 패널
- `실행 기록` 목록·상세·원본 JSON viewer
- API 응답을 직접 파일시스템에서 읽지 않고 Nest API로 조회

### 16.4 `clipper_web_admin`

- 기존 API key 관리 페이지에 필요한 공급자 credential 등록·수정·활성화·테스트 UI 추가
- Naver·OpenAI·Gemini의 현재 등록 경로를 그대로 재사용
- Google Trends RSS·CSV처럼 credential이 없는 수집기는 키 관리 대상에 만들지 않음
- credential 원문은 생성·교체 요청에만 포함하고 목록·상태·테스트 응답에서는 마스킹

## 17. 로컬 API 표면

정확한 경로는 구현 계획에서 기존 controller 관습과 대조하되, 다음 능력이 필요하다.
응답은 전역 envelope 없이 raw object/array를 반환한다.

- 프로필 list/create/update/delete
- 조사 start/list/get/cancel
- 조사 topic list/get
- topic의 영상 후보 생성/start/list/get
- 후보 선택과 상세 video plan 생성
- scene plan과 media decision 조회
- lineage summary/detail 조회
- 실행 기록 list/get
- 저장 JSON 읽기

원본 JSON 조회는 `CLIPPER_DATA_DIR`의 임의 경로를 받지 않는다. opaque artifact ID를
받아 owner·run 범위 안에서 repository가 안전하게 해석한다.

## 18. 오류와 부분 성공

- 조사 출처 하나의 실패가 전체 조사를 자동 실패시키지 않는다.
- 각 SourceFetch 상태와 오류를 저장한다.
- 예상 가능한 source 실패는 failed SourceFetch로 격리한다. unexpected client throw,
  record validation, artifact publish/reload 실패는 source pipeline failure로 run을
  중단하며 ordinary partial로 낮추지 않는다.
- pre-response 실패에는 HTTP status를 발명하지 않고, 불완전 body를 완전 원문이나
  checksum으로 꾸미지 않는다.
- credentialed response의 invalid UTF-8 bytes/base64는 저장하지 않고 exact
  undecodable/withheld 상태와 nonsecret received-body fingerprint만 남긴다. valid UTF-8
  malformed JSON은 safely redacted text와 stored-body checksum을 보존한다.
- A3 parse discriminator는 local artifact에 복사하지 않고 fixed priority로
  status/category/body/parsed branch를 선택하는 데만 쓴다.
- decoded 4xx/5xx의 safe provider 실패 근거는 allowlist 또는 bounded tagged tree로
  저장하되 local parsed success로 꾸미지 않는다. projector가 incomplete PEM이나
  unsafe tree를 만나면 body 전체를 withhold한다.
- 주제를 생성하기에 근거가 부족하면 `partial` 또는 `insufficient`를 표시한다.
- 실패한 공급자를 성공으로 꾸미거나 빈 배열로 조용히 숨기지 않는다.
- LLM JSON parse·schema validation 실패는 원본 응답을 보존하고 새 attempt로 재시도한다.
- 후보 10개 미달이면 부족한 variation을 지정해 한정 재생성한다.
- 미디어 생성 실패는 고정 provider 순서로 넘기지 않고 장면의 의미를 보존하는
  대체 표현을 다시 결정한다.
- 모든 사용자 노출 오류는 기존 AppError·trace 계약을 따른다.

## 19. 검증 전략

### 19.1 저장·계보

- mutable JSON의 temp→file sync→rename→directory sync 원자 교체
- immutable JSON의 temp→file sync→hard-link no-replace 원자 공개
- 중단 실행의 `running`만 `failed` + `process_interrupted`로 복구 표시하고 terminal
  `partial`은 변경하지 않음
- shared classifier 기반 credential·Authorization·민감 query redaction. 실제
  credential-shaped value는 차단하고 natural-language Bearer/Basic 문구는 보존.
  PEM은 full-block linear scan이며 incomplete boundary는 fail closed
- 모든 output reference의 실제 파일 존재
- source→topic→candidate→scene→render lineage 완전성
- 재시도·재실행이 기존 JSON을 덮어쓰지 않음
- opaque ID path traversal 차단

### 19.2 조사

- Google Trends 네 window RSS를 별도 호출·별도 SourceFetch로 기록
- Google Trends RSS의 실제 namespace URI, 다른 prefix, 잘못된 URI,
  DOCTYPE/ENTITY 선언 거부, XML 기본 entity reference decode, 반복 news item fixture
  파싱
- 공식 UI의 영문 exact 5-header sanitized CSV fixture로 BOM, LF/CRLF, quoted
  comma/newline/escaped quote와 `Started/Ended` `sourceText` 기반
  active/ended/unknown 파싱.
  한국어/time/status alias는 실제 capture 전 추측 금지
- 네 window 각각의 pre-response/parse 실패에도 top-level asOf/window와 request hours가
  보존됨
- SourceFetch 모든 union branch의 forbidden field와 Content-Type
  both-or-neither, success/failure/decode/redaction discriminant, response 형태별
  error category
- complete invalid UTF-8의 provider refinement: credential-free Google은 canonical
  padded base64/decode→re-encode/stored checksum, credentialed non-Google은
  base64/raw 없이 withheld/received-body fingerprint
- A3 no-response/incomplete/undecodable/decoded-unparsed/parse-failed/parsed exact
  response-state union과 fatal UTF-8 decode. header 뒤 timeout/abort/oversize는 actual
  accumulated bytes를 보존하고 malformed JSON은 safely redacted text를 보존
- A3 transport-only parse discriminator의 exact priority: undecodable/redaction
  failure가 HTTP보다 먼저, 모든 decoded 4xx/5xx는 http, 2xx parse/content-type/known
  provider/success/schema mismatch를 순서대로 분기하고 local artifact에는
  `parseState` key가 없음
- valid XML과 parsed DTO의 auth scheme/key material/credential-bearing URL을 함께
  deterministic 정제하고 redaction summary를 고정하며, redactor 실패에는 unsafe
  body/checksum/parsed를 생략
- harmless title/sourceText/news URL/snippet 보존, 실제 B1 codec→registry 경로에서
  credential/sentinel 부재와 B1 forbidden key 0건
- shared classifier fixture를 persistence guard/C1/C2 redactor에 공통 적용해
  Authorization header, prefix/JWT/24자 punctuation-mixed/32자 mixed-case Bearer,
  canonical printable `user:password` Basic, credential URL,
  exact/percent/form-sensitive value를 위 regex·threshold 그대로 차단하고
  quoted/single-quoted/equals/malformed-JSON authorization context에서도
  scheme+candidate만 제거한다. key context 없는 `Bearer Stearns outlook`/
  `Basic skincare guide`는 byte/value 그대로 통과하고 provider-specific exception이나
  entropy heuristic은 없음
- linear PEM boundary scanner가 complete one/multiple same-label block 전체를
  `[removed]`로 바꾸고 missing/mismatched/nested/extra/malformed boundary와 5 MiB
  초과 input은 partial output 없이 incomplete. guard는 원문을 reject하고 redactor는
  whole response를 withhold
- decoded/retained-undecodable stored-body checksum, withheld-undecodable
  received-body checksum, artifact wrapper checksum 구분
- durable write→reload→runtime parse 이전에는 소비하지 않고, rejected settlement는
  run failure, fulfilled failed record는 failure collection, succeeded record만
  normalizer 입력이 되는 순서
- 네이버 news/web/blog/initial·discovered DataLab 각각의
  researchRunId/asOf/attempt/signal+query/phase input과 반환 identity equality
- YouTube search 3 lane, lane별 videos 1~50 ID batch, 선택 영상별 single-video
  comments의 개별 fetch→persist→reload와 aggregate adapter 금지
- search/comments는 first page만 호출하며 response `pageCursor`는 근거 표시용 output
  전용. source input/A3 DTO/follow-up 호출에는 cursor 없음
- A3 `ProviderCallAuditV1` wrapper와 `providerCredentialId`/`response.raw`를 직접
  저장하지 않고 success는 Naver 4종·YouTube 3종 exact DTO, failure는 별도
  Naver/YouTube/generic evidence DTO로 projection
- success allowlist의 `nextPageToken→pageCursor` 등 명시 rename, canonical
  `rawBody`/`parsed` deep equality, post-redaction checksum과 logical-field-once
  redaction summary
- 4xx/5xx known failure allowlist와 unknown tagged tree의 exact depth/node/container/
  name/text/64 KiB bounds, forbidden-name drop, omission/redaction/truncation counts.
  safe evidence rawBody/checksum은 actual registry reload 뒤 보존되고 local parsed,
  original sensitive field/value/sentinel은 없음
- 같은 known provider error가 2xx면 provider, unknown 2xx는 validation-withheld이고
  4xx/5xx는 parse state와 무관하게 http
- 각 non-Google source method가 actual B1 codec→registry publish→reload를 통과하고
  transport wrapper/original forbidden key/secret sentinel이 없음
- registry `ShortformDirectorSourceFetchArtifactValidator`가 provider/purpose별
  Google/non-Google refinement를 dispatch하고 forged generic success와 wrong
  schema/lane/phase/videoId를 encode 경계에서 거부
- projection/redaction이 safe body+parsed pair를 만들지 못하면
  `redactionComplete:false` validation failure로 닫고 body/checksum/parsed를 모두 생략
- non-Google expected provider 실패는 failed SourceFetch로 반환되고 unexpected
  client throw/runtime parse/publish/reload rejection은 fixed pipeline failure artifact와
  `publishAndTransitionFailure`로 `failed` 전환을 요청하되 terminal race의 실제 winner는
  보존
- pipeline failure에는 rejection reason/stack이 없고 artifact/manifest/run-index
  fault 직후 status를 단정하지 않음. artifact→run-index reconciliation 뒤 durable
  manifest가 `running`일 때만 `process_interrupted`를 기록하며 failed manifest와
  stale running index는 failed projection으로 복구
- nullable `transitionRunning`은 fixed typed terminal conflict로 표면화하고
  cancel/external terminal winner의 durable manifest를 reload해 보존
- owner/run single execution lease, archive-vs-snapshot admission, cancel-vs-failure
  compare-and-transition race
- common abort-or-terminal gate를 source fetch admission/wave 직후, synchronous
  parse·rank·normalize·validate stage, query-plan/source-normalization/
  YouTube-reference-analysis/topic-synthesis 전후, publication 전, final transition
  전에 적용. 네 inference port가 signal을 실제 transport에 전달하고 provider 반환 뒤
  cancel이 이기면 새 LLM/output attach가 없음
- `order=date`가 기본 수집에 없음을 고정
- 채널 다양성·중복 제거·시간당 조회 계산
- 각 출처 단독 신호도 topic 후보가 될 수 있음
- 오래된 인기 자료가 현재성 점수를 얻지 않음
- 공식 사실과 시장 관측 역할 분리

### 19.3 LLM

- 같은 frozen ResearchSnapshot으로 모델 비교
- 구조화 output contract
- 최소 10개 영상 후보
- 중복·근거 없는 후보 검출
- prompt·raw response·parsed response·usage 저장
- 현재 `gpt-4.1` 기준선과 새 모델 결과 비교

### 19.4 UI

- 각 주제·후보·장면의 `근거·과정` 연결
- 패널 탭의 summary와 raw JSON 일치
- 일반 화면은 원본 상세가 닫힌 상태에서도 사용 가능
- 실행 기록 필터와 부모·자식 timeline
- 부분 실패·재시도 표시
- 다크·라이트 Material 토큰 준수

### 19.5 실제 결과물

- 실제 최신 조사로 주제 생성
- 선택 주제에서 실제 최소 10개 후보
- 한 후보를 끝까지 제작
- 실제 TTS·이미지·영상 공급자 사용
- Omni·Veo 비교
- 이전 결과와 블라인드 품질 비교
- 비용·지연·실패율 기록

## 20. 구현 순서의 제약

전체 목표는 하나의 end-to-end 결과물이지만 구현은 다음 의존 순서를 따른다.

1. 로컬 run storage·lineage 계약
2. 프로필과 병렬 조사
3. 주제와 최소 10개 영상 후보
4. `근거·과정`과 `실행 기록`
5. 선택 후보의 장면·미디어 결정
6. 실제 이미지·영상 공급자 비교
7. Motion Canvas 결과물과 품질 비교

각 단계는 이전 단계의 실제 JSON을 입력으로 사용한다. UI fixture만 연결한 상태를
완료로 간주하지 않는다.

## 21. 재검토 트리거

- Google Trends 알파 테스터 선정 통보
  - `GoogleTrendsProvider`에 공식 API 구현을 추가하고 RSS·CSV와 비교한다.
- RSS·CSV와 네이버 데이터랩만으로 임의 키워드 추이가 부족하다는 실제 사례
  - HTML 추출 도입 여부를 별도 검토한다.
- 모델 benchmark에서 초기 기본 모델이 비용 대비 열세
  - 역할별 model ID를 변경한다.
- 로컬 JSON 실행 수가 많아져 목록 조회가 실제로 느려짐
  - 측정 후에만 index 분할 또는 경량 색인을 검토한다.
- 공통 플러그인 내부 사이드바가 제품 차원에서 확정됨
  - AI Director 임시 사이드바를 공통 컴포넌트로 교체한다.

## 22. 완료 정의

다음이 한 번의 실제 실행에서 모두 확인돼야 한다.

- 사용자가 운영 프로필을 선택하고 별도 자료 첨부 없이 조사를 시작한다.
- 필요한 Naver·OpenAI·Gemini·YouTube credential을 기존 관리자 페이지에서 등록·검사할
  수 있고, 어떤 credential도 Electron 빌드·환경 파일·로컬 실행 JSON에 저장되지 않는다.
- 기존 AI Director 전략·영상 구성의 크레딧 확인 UI와 차감·환불 호출이 제거되고, 새
  조사·후보·미디어·품질 검사 경로도 크레딧 operation을 만들지 않는다.
- Google Trends RSS·네이버·YouTube가 각각 호출되고 로컬 JSON으로 남는다.
- 실패한 출처는 실패 상태로 보이고 나머지 결과는 계속 처리된다.
- 조사 시점에 맞는 여러 주제가 근거 ID와 함께 표시된다.
- 한 주제에서 서로 다른 영상 후보가 최소 10개 표시된다.
- 모든 주제·후보에서 `근거·과정`을 열어 원본 API와 LLM 기록까지 볼 수 있다.
- 한 후보가 장면별 적합한 표현을 사용해 실제 영상으로 렌더된다.
- 렌더 시작 시 기존 보관함의 공용 작업 큐에 나타나고, 성공한 MP4가 기존 보관함에서
  재생된다.
- 완성 영상에서 장면별 근거·미디어 결정·생성 prompt·품질 결과를 추적할 수 있다.
- `실행 기록`에서 전체 run과 모든 JSON을 조회할 수 있다.
- 기존 로컬 프로젝트와 사용자의 기존 변경을 훼손하지 않는다.
