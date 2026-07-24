# AI 숏폼 디렉터 — Vira 검증 corpus 확보 선택지

작성일: 2026-07-24 KST

상태: 선택지 정리 완료 · 제품 방향 결정은 다음 세션으로 보류

## 1. 결론부터 바로잡기

현재 Vira 서비스와 DB를 그대로 조회해서는 AI 숏폼 디렉터의 `V` 입력 축을 평가할 수
없다.

- Vira는 아직 개발 중인 서비스다.
- 현재 DB에는 폭넓고 대표성 있는 시장 corpus가 아니라 소량의 테스트 데이터만 있다.
- 특정 주제의 row가 없더라도 시장 수요가 없다는 뜻이 아니라 아직 수집하지 않았다는
  뜻이다.
- 현재 데이터로 주제 간 결과를 비교하면 입력 축의 효용과 수집 coverage 부족을 혼동한다.

따라서 2026-07-24에 준비한 기존 `shorts_*` read-only SQL은 실제 DB에 실행하지 않았다.
현재 case pack의 Vira 상태도 `provider_not_called`와 빈 evidence로 유지한다. 이를
`insufficient`로 바꾸면 실제 조회를 수행했거나 대표 corpus에서 관측이 부족했던 것처럼
오해할 수 있으므로 바꾸지 않는다.

## 2. 현재 Vira 코드에서 확인한 경계

읽기 전용 재확인 기준:

```text
repo: /Users/jina/project/vira
branch: main
HEAD: 5267ac0bcc6bde9020bd35f67e27dc375d0a00ef
worktree: clean
```

Vira에는 서로 다른 두 수집 계열이 공존한다.

### 2.1 `shorts_*`: yt-dlp 중심 실험·legacy 계열

주요 코드:

- `src/lib/db/schema/shorts.ts`
- `src/lib/shorts/ytdlp.ts`
- `src/lib/shorts/ingest.ts`
- `src/lib/shorts/snapshot.ts`
- `scripts/shorts-collect-upload.ts`

특징:

- 키워드로 후보를 찾고 yt-dlp `info.json`을 적재한다.
- `shorts_videos`, `shorts_snapshots`, `shorts_comments`에 저장한다.
- 댓글, 자막과 비교적 풍부한 메타데이터를 다룬다.
- orchestration script는 local 또는 snapshot DB만 허용하는 안전가드를 가진다.

이번 세션에서 만든 read-only SQL은 이 테이블들을 대상으로 했지만, 현재 데이터가
대표 corpus가 아니므로 실제 품질 평가에는 사용할 수 없다.

### 2.2 `intel_market_*`: YouTube Data API 기반 현재 시장 pool 계열

주요 코드:

- `src/lib/keyword-search/youtube-adapter.ts`
- `src/lib/intel/market/discovery/keyword-search.ts`
- `src/lib/intel/market/discovery/trending.ts`
- `src/lib/intel/market/discovery/enrich-metadata.ts`
- `src/lib/intel/market/discovery/admit.ts`
- `src/lib/intel/market/snapshot/video.ts`
- `src/lib/db/schema/intel-market-pool.ts`
- `src/lib/inngest/functions/intel-market-discovery-cron.ts`
- `src/lib/inngest/functions/intel-market-video-snapshot-cron.ts`

이미 다음 기반이 있다.

- 지역·언어·최근 기간·키워드 기반 YouTube 검색
- `videos.list` 메타데이터와 공개 통계 보강
- discovery source, seed, rank 기록
- 영상·채널 pool
- 일별 view/like/comment snapshot
- view velocity와 engagement 계산
- 추적 빈도와 상태 관리

따라서 새로운 수집기를 완전히 별도로 만드는 것보다 이 경로를 실험용으로 격리해
보완하는 선택지가 유력하다. 단, 코드가 존재한다는 사실은 서비스와 데이터가 완성됐다는
뜻이 아니다.

## 3. 현재 코드에서 다음 설계 전에 확인할 문제

### 3.1 Shorts 판별

현재 discovery gate는 길이 180초 이하와 한국어 여부를 중심으로 판별한다. 그러나
YouTube Data API의 `videoDuration=short`는 실제 Shorts가 아니라 4분 미만 영상을 뜻한다.
현재 YouTube Shorts는 업로드 시점 조건과 함께 정사각형 또는 세로 화면비, 최대 3분
조건을 가진다.

따라서 Data API 검색 뒤 다음 중 하나로 실제 Shorts 여부를 별도 확인해야 한다.

- 승인된 metadata-only 보강으로 width/height를 확인
- 공식 Shorts URL/표면에서 확인 가능한 신뢰도 높은 판별 계약 도입
- 사람 검토가 가능한 작은 shortlist만 별도 확인

길이만으로 `/shorts/<id>` URL을 저장하는 현재 가정은 검증 corpus에서 그대로 사용하지
않는다.

공식 자료:

- [YouTube Data API `search.list`](https://developers.google.com/youtube/v3/docs/search/list)
- [YouTube 3분 Shorts 기준](https://support.google.com/youtube/answer/15424877?hl=en)

### 3.2 API quota 모델

현재 Vira code/comment는 `search.list`를 호출당 100 units로 계산한다. 2026-06-01 갱신된
공식 문서는 `search.list`에 별도 일일 100회 기본 bucket을 두고 각 호출을 1 unit으로
설명한다. 실제 구현 전에는 Google Cloud Console의 해당 프로젝트 quota와 공식 문서를
함께 확인하고 quota bookkeeping과 ceiling을 맞춰야 한다.

- [YouTube Data API quota calculator](https://developers.google.com/youtube/v3/determine_quota_cost)

### 3.3 보관·파생 지표 정책

비인가 YouTube API data는 원칙적으로 30일 안에 삭제하거나 갱신해야 한다. 영상 원본의
download, cache와 장기 보관은 별도 정책 경계를 가진다. 2026-06부터 파생 지표와 장기
통계 보관에는 추가 정책과 승인 절차도 존재한다.

따라서 검증 DB는 영구 raw warehouse가 아니라 다음을 가진 만료 가능한 연구 corpus로
설계해야 한다.

- retrieval과 refresh 시각
- source API와 query manifest
- 30일 refresh/delete 정책
- raw metadata와 실험용 파생값의 분리
- 사용자 화면에 노출할 때 source와 관측 시점 표시

공식 자료:

- [YouTube API Services Developer Policies](https://developers.google.com/youtube/terms/developer-policies)
- [Additional policies for derived metrics and data storage](https://developers.google.com/youtube/terms/derived-metrics-policy)

### 3.4 yt-dlp 사용 경계

yt-dlp는 현재 Vira의 legacy metadata/comments 수집에 쓰이지만 YouTube 측 PO Token,
rate limit, cookie와 계정 제한에 민감하다. 대량 discovery나 영상 원본 저장의 기본
provider로 두지 않는다.

다음 세션에서 정책·권리 경계를 승인한다면 다음처럼 제한적으로 검토할 수 있다.

- 공식 API로 먼저 좁힌 소수 shortlist
- `--skip-download` metadata-only 확인
- 로그인 cookie나 사용자 계정에 의존하지 않는 범위
- 원본 영상, audio와 frame을 보관하지 않는 범위

- [yt-dlp YouTube extractor 안내](https://github.com/yt-dlp/yt-dlp/wiki/Extractors)

## 4. 다음 세션에서 비교할 세 가지 접근

### 접근 A — Vira feature branch + 격리된 실험 DB

현재 권장 후보지만 아직 사용자 결정은 아니다.

```text
Vira 새 branch/worktree
  → 기존 YouTube Data API discovery 재사용·보완
  → 운영 RDS와 분리된 local experiment Postgres
  → 반복 snapshot
  → quality-input `vira-evidence.v1` export adapter
```

장점:

- Vira가 실제로 발전해야 할 코드 경로를 검증한다.
- discovery, pool, snapshot 코드를 중복 구현하지 않는다.
- 운영 데이터와 실험 데이터를 분리한다.
- 실험에서 확인한 변경을 나중에 Vira product로 가져갈 수 있다.

비용과 조건:

- branch/worktree 생성, schema 변경과 local DB 준비가 필요할 수 있다.
- migration, DB 실행과 YouTube API 호출은 각각 사용자 승인이 필요하다.
- 현재 quota와 API data policy를 반영한 설계 보정이 선행돼야 한다.

### 접근 B — `.codex` 또는 별도 연구 저장소의 독립 collector

장점:

- Vira product 개발과 완전히 격리된다.
- 품질 입력 아키텍처만 빠르게 검증할 수 있다.

단점:

- Vira의 discovery·snapshot 코드를 중복 구현한다.
- 실험 결과가 Vira 구현의 검증으로 직접 이어지지 않는다.
- 나중에 adapter와 migration 작업이 한 번 더 필요하다.

AI 숏폼 디렉터의 입력 구조만 검증하고 Vira 제품 개발은 별도 일정으로 둘 때 선택할 수
있다.

### 접근 C — 사용자 URL 목록 + yt-dlp 중심 수동 corpus

장점:

- API discovery를 만들기 전에 빠르게 소수 사례를 볼 수 있다.
- 사용자가 중요하게 보는 영상만 포함할 수 있다.

단점:

- 선택 편향이 매우 크다.
- 최신성과 비교군 대표성이 없다.
- 사용자 부담이 크다.
- yt-dlp 안정성·정책 경계에 의존한다.

정식 `V` 축 평가보다는 UI나 evidence envelope의 작은 usability test에만 적합하다.

## 5. 최신 검색어가 필요한 범위

두 실험 목적을 구분한다.

### 5.1 `P/S/A/R/F` 입력 구조 검증

당일 최고 인기 검색어가 필수는 아니다.

- 공식 source와 정답 기준이 안정적이어야 한다.
- 같은 pack을 여러 조건과 평가자에게 반복해야 한다.
- 실험 도중 관심도와 사실관계가 급변하면 입력 효과와 사건 효과를 구분하기 어렵다.

따라서 현재 네 사례와 source pack은 이 축들의 계약·평가 fixture로는 계속 사용할 수
있다. 다만 최종 대표 사례인지는 다음 설계에서 다시 판단한다.

### 5.2 `V` 시장 신호 검증

최근에 실제로 활동이 있는 주제가 필요하다. 그러나 “오늘 가장 뜬 단어” 자체가 목표는
아니다. 다음 조건을 충족하는 **최근이면서 충분히 관측 가능한 주제**가 더 적합하다.

- 최근 30일 내 유효 Shorts 30개 이상
- 서로 다른 채널 10개 이상
- 최근 7~14일에도 신규 업로드가 있음
- 한 채널, 한 사건이나 팬덤 하나에 과도하게 편중되지 않음
- view/like/comment 공개 통계를 반복 관측할 수 있음

Google Trends `Trending now`는 뉴스성 Google Search 급등을 보여주므로 YouTube Shorts
수요와 동일시하지 않는다. 후보 seed 생성에만 쓰고, YouTube API의 실제 coverage와
채널 다양성으로 최종 선택한다.

- [Google Trends `Trending now` 안내](https://support.google.com/trends/answer/3076011?hl=en)
- [YouTube `videos.list` mostPopular](https://developers.google.com/youtube/v3/docs/videos/list)

## 6. 잠정 수집 설계

다음 수치는 다음 세션에서 승인·수정할 초안이지 확정 사양이 아니다.

1. 사용자가 실험 범위를 선택한다.
   - 광고 제작과 연결되는 업종 중심
   - 한국 YouTube Shorts 전체 트렌드
2. 분야별 현재 후보 query 5~10개를 만든다.
3. 최근 30일을 `date`와 `viewCount` 두 ordering으로 검색한다.
4. API 결과를 dedupe하고 한국어, 실제 Shorts, 공개 통계와 채널 다양성으로 거른다.
5. coverage gate를 통과한 주제만 최종 사례로 선정한다.
6. 주제별 40~60개, 전체 160~240개 정도의 작은 균형 panel을 만든다.
7. 수집일, 1일, 3일, 7일에 snapshot을 기록한다.
8. 초기 실험은 댓글 본문·작성자·영상 원본을 수집하지 않는다.
9. snapshot을 frozen `V` evidence로 export하고 그 뒤에만 입력 조합 실험을 실행한다.

한 번의 조회수는 `market.video-observation`에는 쓸 수 있지만 성장 신호를 증명하지 않는다.
`market.peer-growth`는 최소 3개 시점이 생긴 뒤에만 만든다.

## 7. 다음 세션에서 먼저 결정할 질문

순서대로 하나씩 결정한다.

1. corpus 목적은 광고 제작 업종 중심인가, 한국 Shorts 전체 트렌드인가?
2. 접근 A와 B 중 어디에 수집 코드를 둘 것인가?
3. 실제 YouTube API data를 보관·표시할 제품 범위가 정책상 허용되는가?
4. 분야, query 후보 생성 방법과 coverage gate는 무엇인가?
5. snapshot 기간과 panel 규모는 얼마인가?
6. Vira `V` 축이 준비되기 전 기존 품질 실험은 어디까지 실행할 것인가?

이 결정 전에는 다음 작업을 시작하지 않는다.

- 현재 Vira DB 조회
- Vira branch/worktree 생성이나 코드 수정
- migration 또는 local/remote DB 실행
- YouTube Data API와 yt-dlp 실제 호출
- 생성 provider 호출
- 기존 네 주제를 Vira collection seed로 확정
