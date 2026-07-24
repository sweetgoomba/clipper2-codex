# AI 숏폼 디렉터 — 품질 입력 아키텍처 검증 프로토콜

작성일: 2026-07-24 KST

상태: Task 1~3 offline 기반 검증 완료 · 실제 Vira corpus 전략 결정 대기

현재 단계: frozen source pack과 offline 계약은 검증했다. production 코드·목업·현재 Vira
DB·YouTube API·yt-dlp·생성 provider 실행은 시작하지 않는다.

## 0.1 2026-07-24 세션 종료 보정

이 문서의 초기 설계는 현재 Vira DB에서 네 주제의 대표 market evidence를 얻을 수 있다고
가정했다. 사용자가 다음 실제 상태를 확인해 이 가정을 철회했다.

- Vira는 아직 개발 중인 서비스다.
- 현재 DB는 폭넓고 대표적인 market corpus가 아니라 소량의 테스트 데이터다.
- row 부재는 시장 신호 부재가 아니라 수집 coverage 부재일 가능성이 크다.

따라서 현재 Vira DB read는 실행하지 않으며, `V` 축의 실제 품질 실험도 대표 corpus를
새로 확보하기 전까지 보류한다. 기존 read-only SQL과 normalizer는 fixture 기반 통합 계약,
보안과 failure atomicity 검증용으로만 보존한다.

다음 세션에서는 아래 문서의 선택지를 먼저 결정한다.

- `SHORTFORM_DIRECTOR_VIRA_VALIDATION_CORPUS_OPTIONS_2026-07-24.md`

이 보정은 `P/S/A/R/F` 가설이나 rubric을 폐기하지 않는다. 다만 현재 네 사례와 Vira
테스트 DB를 연결해 `V` 효과를 판단하지 않는다.

## 0. 문서 목적

이 문서는
`SHORTFORM_DIRECTOR_QUALITY_INPUT_ARCHITECTURE_AND_DIRECTOR_BRIEF_DESIGN_2026-07-21.md`에서
제안한 품질 입력이 실제로 숏폼 기획 품질을 높이는지 검증하는 방법을 정의한다.

이번 검증에서 답할 질문은 세 가지다.

1. 운영 프로필, 공식 자료, 시청자 질문, Vira 관측, 크리에이티브 레퍼런스와 과거
   피드백이 각각 어떤 품질을 개선하는가.
2. 품질 향상이 입력 수집 비용과 사용자 부담을 정당화하는가.
3. 어떤 입력을 기본값, 조건부 입력, 제외 대상으로 분류해야 하는가.

이 문서는 영상 renderer의 품질이나 실제 조회 성과를 검증하지 않는다. 먼저
`Content Opportunity → Director Brief → 45초 대본 → 5~7개 beat storyboard`까지의
기획 품질을 검증한다.

## 1. 이번 문서에서 고정하는 결정

### 1.1 네 가지 실제 사례

한 종류의 콘텐츠에서만 잘 작동하는 입력 구조를 만들지 않도록 서로 다른 운영 경로를
선택한다.

| 사례 ID | 운영 경로 | 실제 주제 | 고정 episode A 질문 |
|---|---|---|---|
| `BEAUTY-01` | 브랜드리스 큐레이션 | 젤광 립 틴트 비교 | 같은 젤광 틴트라도 색, 광택, 착색, 입술 상태에 따라 무엇을 확인해야 하는가? |
| `PRODUCT-01` | 제품 마케팅 | 스마트카라 400 Pro 2 구매 전 확인 | 용량 외에 처리시간, 필터, 투입 제한, 보조금을 어떻게 확인해야 하는가? |
| `IDOL-01` | 엔터테인먼트 해설 | LE SSERAFIM `CELEBRATION` | 공식 설명의 “변화를 받아들이고 앞으로 나아가는 순간을 축하한다”는 메시지가 공식 콘텐츠에서 어떻게 표현되는가? |
| `EXPERT-01` | 전문가 교육 | 채권 가격과 시장금리 | 시장금리가 3%에서 4%로 오르면 기존 3% 고정금리 채권의 가격은 왜 내려가는가? |

이 네 주제는 `P/S/A/R` source pack과 평가 계약을 검증하는 fixture다. 최신 Vira market
corpus의 collection seed나 최종 대표 사례로 확정된 것이 아니다. 실제 `V` 축을 검증할
주제는 승인된 수집 경로에서 최근 coverage와 채널 다양성을 측정한 뒤 다시 선택한다.

### 1.2 비교할 입력 축

입력 축은 다음 여섯 개다.

| 축 | 의미 | 대표 검증 질문 |
|---|---|---|
| `P` Profile | 운영 목적, 시청자, 톤, 금지사항 | 결과가 실제 운영자와 대상 시청자에게 맞아지는가? |
| `S` Source | 공식·권위 자료와 근거 위치 | 구체성과 사실 정확도가 높아지는가? |
| `A` Audience | 반복되는 질문·오해·원하는 변화 | 시청자 관련성과 hook이 좋아지는가? |
| `V` Vira | 현재 시장·콘텐츠 관측 snapshot | 시의성이나 비자명한 기회가 추가되는가? |
| `R` Reference | 구조·리듬·시각 표현 패턴 | 시각화 가능성과 전개가 좋아지는가? |
| `F` Feedback | 이전 편의 승인·수정·실패 기억 | 다음 편에서 같은 실수를 줄이는가? |

Vira는 사실의 근거가 아니라 시장 관측이다. Vira 값이 충분하지 않을 때
`insufficient`를 정직하게 전달하는 것 역시 검증 대상이다.

### 1.3 source pack은 실행 중 검색하지 않는다

모든 입력은 실행 전에 동결한 source pack에서만 가져온다. 같은 조건의 반복 실행 도중
검색 결과, 댓글, 상품 페이지 또는 Vira 값이 바뀌어서는 안 된다.

현재 문서의 URL 목록은 **source inventory**다. 실제 실험 가능한 frozen pack이 되려면
원문 추출, 근거 위치, 수집 시각, digest와 권리 표기가 채워져야 한다. 존재하지 않는
digest나 Vira 수치를 문서에서 미리 만들지 않는다.

## 2. 검증 가설

### 2.1 품질 가설

- `P`는 대상 적합성과 제작 제약 준수를 높인다.
- `S`는 구체성, 근거 정확성, payoff를 높이고 허위 주장을 줄인다.
- `A`는 시청자 관련성과 hook-payoff 연결을 높인다.
- `V`는 시의성과 기회 발견을 높이지만 모든 주제에 이득을 주지는 않는다.
- `R`은 정보 자체보다 beat 구성과 시각화 가능성을 높인다.
- `F`는 같은 결과의 수정이 아니라 다음 자매 episode에서 반복 오류를 줄인다.

### 2.2 비용 가설

모든 입력을 항상 요구하는 구조는 품질 이득보다 사용자 부담이 커질 수 있다. 따라서 각
입력은 품질 점수와 함께 다음 비용을 기록한다.

- 사용자 입력 시간
- source 수집·정리 시간
- 입력 token 수
- 생성 token 수
- 수집 실패 또는 부족 상태
- 실제 실행 시 provider latency와 비용

### 2.3 반증 조건

다음 결과가 나오면 “입력이 많을수록 좋다”는 가설을 기각한다.

- 새 입력을 더했지만 목표 품질 차원이 반복적으로 좋아지지 않는다.
- 점수는 비슷한데 사용자 부담이나 token 비용만 크게 증가한다.
- 새 입력 때문에 근거 계층이 섞이거나 핵심 메시지가 흐려진다.
- Vira가 약한 주제에서 모델이 관측값을 과장하거나 만들어 낸다.
- 레퍼런스를 추가한 결과 사실이나 표현을 베끼는 방향으로 퇴행한다.

## 3. frozen source pack 계약

### 3.1 pack 단위

각 사례는 다음 구조를 가진다.

```text
case pack
  ├─ profile card
  ├─ episode A intent
  ├─ episode B intent
  ├─ official / authoritative sources
  ├─ audience question set
  ├─ Vira snapshot or explicit insufficient state
  ├─ creative pattern cards
  └─ feedback cards, episode A 평가 뒤 생성
```

한 source record의 필수 필드는 다음과 같다.

| 필드 | 의미 |
|---|---|
| `pack_id` | 사례 pack의 안정적인 ID |
| `source_id` | pack 안에서 중복되지 않는 ID |
| `source_class` | `official_fact`, `authority_explanation`, `audience_observation`, `market_observation`, `creative_pattern`, `editorial_interpretation`, `ai_hypothesis` 중 하나 |
| `title` | 사람이 식별할 수 있는 원문 제목 |
| `original_url` | 원문 주소 |
| `publisher` | 발행 주체 |
| `published_at` | 확인 가능한 경우의 발행 시각 |
| `retrieved_at` | source pack 수집 시각 |
| `cutoff_at` | 이 실험이 허용하는 최신 관측 시각 |
| `content_digest` | 실제 원문을 materialize한 뒤 계산한 digest |
| `evidence_locator` | 페이지, 문단, timestamp 또는 구조화 필드 경로 |
| `permitted_use` | `fact`, `audience`, `market`, `creative`, `editorial` 중 허용 용도 |
| `rights_note` | 원문 인용·화면 사용·변형 가능 여부와 확인 상태 |
| `availability` | `verified`, `partial`, `insufficient`, `unavailable`, `provider_not_called` |
| `notes` | 조건, 시점 제한, 해석 위험 |

`content_digest`가 없거나 `evidence_locator`가 비어 있는 source는 inventory일 뿐 실험 입력이
아니다.

### 3.2 증거 계층

다음 계층은 prompt와 평가 화면에서도 섞지 않는다.

1. **공식 사실**: 브랜드, 기관, 아티스트 소속사의 명시적 정보
2. **권위 설명**: 규제기관·공공기관 등의 교육 자료
3. **시장 관측**: Vira가 반환한 video, growth, comment cluster 등의 관측
4. **시청자 관측**: 공개 질문·댓글·리뷰를 비식별·요약한 내용
5. **크리에이티브 패턴**: 구조, 리듬, 화면 문법에 대한 참고
6. **편집 해석**: 매체나 편집자의 분석
7. **AI 가설**: 위 자료를 조합해 생성한 검증 전 아이디어

시장 관측, 시청자 반응, 편집 해석과 AI 가설은 공식 사실로 승격할 수 없다. 상관관계를
인과관계로 바꿀 수도 없다.

### 3.3 pack 크기 제한

자료가 많은 조건 자체가 유리해지는 문제를 줄이기 위해 다음 상한을 둔다.

| 구성 | 상한 |
|---|---|
| 공식·권위 source | 사례당 3~5개 |
| audience question | 비식별·의미 중복 제거 후 10개 |
| Vira evidence | 사례당 최대 5개 관측 |
| creative pattern card | 사례당 최대 2개 |
| feedback card | 사례당 최대 3개 |

source 원문 전체를 prompt에 넣지 않는다. 각 source에서 이번 episode에 필요한 claim과
evidence locator만 뽑은 evidence card를 사용한다.

### 3.4 Vira snapshot 제한

Vira 입력은 기존 `vira-evidence.v1` 설계를 그대로 따른다.

- 현재 활성 경로의 `market.video-observation`과 lab 경로의 `market.peer-growth`만 후보로
  사용한다.
- `legacy.market-format-hook`과 `legacy.keyword-viral-report`는 현재 입력에서 제외한다.
- `evidenceClass`, `lifecycle`, `materializedAt`, `window`, `sampleSize`,
  `observation.state`, `method`를 보존한다.
- 공통 confidence를 새로 만들지 않는다. `sufficient`, `partial`, `insufficient`,
  `unavailable`을 score로 변환하지 않는다.
- Vira DB row를 직접 prompt에 넣거나 아직 없는 Clipper 연동 API가 있다고 가정하지
  않는다.

실제 snapshot을 만들 때는 keyword별 상위 결과를 그대로 많이 넣지 않고 이번 episode와
관련된 최대 5개 evidence만 선택한다. 조회 결과가 부족하면 빈자리를 legacy 값이나 AI
추정으로 채우지 않는다.

### 3.5 축 사이 정보 누출 방지

하나의 원문이 사실과 크리에이티브 패턴을 모두 제공할 수 있어도 card는 분리한다.

- `C2`의 source card에는 claim, 짧은 extract와 locator만 들어간다.
- `C3`의 audience card는 질문·오해만 담고 제품 사실이나 인기도 수치를 추가하지 않는다.
- `C4`의 Vira card는 관측과 산출 방법만 담고 생성 지시를 추가하지 않는다.
- `C5`의 reference card는 화면 구조·리듬·표현 패턴만 담고 새 사실 claim을 추가하지
  않는다.

예를 들어 스마트카라 brochure의 규격 text는 `P-S01`, 비교표 layout은 `P-R01`로 나눈다.
`C2`에서 layout을 먼저 보여주지 않고 `C5`에서만 reference pattern을 보여준다.

## 4. 사례별 source pack

현재 공통 cutoff는 `2026-07-24 KST`다. 공개 URL은 이날 확인했지만 원문 파일과 Vira
snapshot은 아직 frozen artifact로 materialize하지 않았다.

아래 운영 프로필은 실제 조직을 사칭하거나 제휴를 전제하지 않는 **평가용 역할
설정**이다. audience question 목록도 현재는 사전 등록한 질문 intent다. 실제 관측 근거로
사용하려면 materialization 단계에서 공개 원문 locator와 연결해야 한다.

### 4.1 BEAUTY-01 — 젤광 립 틴트 비교

#### 운영 프로필

- 운영자: 특정 브랜드를 대변하지 않는 뷰티 큐레이션 채널
- 시청자: 온라인 발색표만으로 구매를 결정하기 어려운 입문자
- 목표 행동: 저장 후 자신의 입술 상태·원하는 마무리에 맞춰 후보를 좁힌다.
- 톤: 빠르지만 단정 짓지 않고 비교 조건을 먼저 밝힌다.
- 금지: “모든 웜톤/쿨톤에게 맞는다”, 실제 사용 없이 지속력·건조함을 확정하는 표현,
  생성 이미지로 실제 발색을 재현했다는 인상

#### 고정 질문

- episode A: 같은 “젤광” 틴트라도 색, 광택, 착색, 입술 상태에 따라 무엇을 확인해야
  하는가?
- episode B: 공식 컬러표와 실제 발색이 다를 수 있는 이유를 설명할 때 어떤 조건을 먼저
  밝혀야 하는가?

#### source inventory

| ID | 분류와 허용 용도 | 이번 검증에서 추출할 것 | 현재 상태 | 원문 |
|---|---|---|---|---|
| `B-S01` | 공식 사실 · `fact` | 제품명, 색상 option, 브랜드가 명시한 사용 정보 | URL·본문 일부 확인, 원문 추출 전 | [rom&nd 더 쥬시 래스팅 틴트 레어시리즈](https://romand.co.kr/product/detail.html?product_no=994) |
| `B-S02` | 공식 사실 · `fact` | 제품명, 색상 option, 브랜드 설명 | URL 확인, 상세 이미지 추출 전 | [AMUSE 젤핏 틴트](https://amusemakeup.com/product/%EC%A0%A4%ED%95%8F-%ED%8B%B4%ED%8A%B8-12%EC%A2%85-%ED%83%9D1/359) |
| `B-S03` | 공식 사실 · `fact` | 4 ml, 공식 사용법, 브랜드가 설명한 젤 광 layer·착색 | 검색 본문 확인, 원문 추출 전 | [hince 로 글로우 젤 틴트](https://www.hince.co.kr/product/%EB%A1%9C-%EA%B8%80%EB%A1%9C%EC%9A%B0-%EC%A0%A4-%ED%8B%B4%ED%8A%B8/1112/) |
| `B-A01` | 시청자 관측 · `audience` | 공식몰 공개 후기에서 발색 차이, 시간 경과, 입술 바탕색 관련 질문을 비식별 요약 | materialize 전 | 위 세 공식몰의 공개 후기 영역 |
| `B-R01` | 크리에이티브 패턴 · `creative` | 한 화면에 비교 조건과 swatch 순서를 고정하는 구성 | pattern만 허용 | [Lululand 비교 형식](https://lululandtvblog.blogspot.com/2022/04/romand-blur-fudge-tint-910-11-swatches.html) |
| `B-R02` | 크리에이티브 패턴 · `creative` | 개인 입술 조건을 먼저 밝히고 제품별 관찰을 나누는 구성 | pattern만 허용 | [Janel K 비교 형식](https://www.janelku.com/2024/09/makeup-staples-rom-juicy-lip-tint-and.html) |
| `B-V01` | 시장 관측 · `market` | `메이크업`, `립`, `틴트`, `젤광` 관련 최대 5개 관측 | `provider_not_called` | Vira read-only snapshot |

#### 고정 audience question set

실험 입력에는 원문 계정명과 문장을 넣지 않고, materialization 뒤 source locator를
연결할 다음 10개 의미 단위로 정규화한다.

1. 공식 색상표와 내 입술 위 발색이 다른 이유는 무엇인가?
2. 원래 입술색이 진하거나 푸를 때 어떤 정보를 먼저 봐야 하는가?
3. 바른 직후와 시간이 지난 뒤 색이 달라지는가?
4. 광택이 남는 것과 착색이 남는 것은 어떻게 다른가?
5. 각질이나 건조함이 있을 때 결과가 어떻게 달라질 수 있는가?
6. 한 번 바른 발색과 여러 번 겹친 발색을 어떻게 비교해야 하는가?
7. 음식이나 음료 뒤에 무엇을 다시 확인해야 하는가?
8. 덧바를 때 색이 탁해지지 않게 하려면 무엇을 봐야 하는가?
9. 조명과 카메라 보정이 swatch 판단에 어떤 영향을 주는가?
10. “웜톤용/쿨톤용” 한 문장 대신 어떤 조건을 함께 알려줘야 하는가?

이 질문들은 source materialization 뒤 실제 관측과 연결해야 하며, 연결되지 않은 문항은
일반 독자 질문으로 표시한다.

#### 필요한 시각 증거

- 같은 조명·같은 도포 횟수·같은 시간 경과를 표시한 비교 grid
- `색 / 광택 / 착색 / 입술 상태` 네 축의 체크 카드
- 실제 swatch가 없을 때는 색을 생성해 대체하지 않고 공식 제품 이미지와 설명 도식으로
  범위를 제한한다.

### 4.2 PRODUCT-01 — 스마트카라 400 Pro 2 구매 전 확인

#### 운영 프로필

- 운영자: 스마트카라 제품 마케팅 팀
- 시청자: 1~2인 가구에서 음식물처리기 구매를 검토하는 사람
- 목표 행동: 자신의 사용량, 설치 환경, 유지관리와 거주지 지원 조건을 확인한 뒤 상담
  또는 구매 검토를 이어간다.
- 톤: 장점을 설명하되 제한 조건과 지역·시점 차이를 숨기지 않는다.
- 금지: “냄새 완전 제거”, 근거 없는 경쟁 우위, 모든 지자체가 같은 보조금을 준다는 표현

#### 고정 질문

- episode A: 스마트카라 400 Pro 2를 구매하기 전에 용량 외에 처리시간, 필터, 투입 제한,
  보조금을 어떻게 확인해야 하는가?
- episode B: 2 L와 5 L 음식물처리기 중 우리 집에 맞는 용량을 고를 때 어떤 사용 패턴을
  확인해야 하는가?

#### source inventory

| ID | 분류와 허용 용도 | 이번 검증에서 추출할 것 | 현재 상태 | 원문 |
|---|---|---|---|---|
| `P-S01` | 공식 사실 · `fact` | 2 L, 건조·분쇄 방식, 공식 처리시간 범위, 기능과 설치 방식 | PDF 확인, page locator 추출 전 | [SMARTCARA 2024 brochure](https://smartcara.com/web/upload/download/SMARTCARA_2024_Brochure.pdf?v3=) |
| `P-S02` | 공식 사실 · `fact` | 모델 `SC-D0208`, 사용·안전·투입 제한, 관리 방법 | 첨부 manual 존재 확인, 원문 추출 전 | [400 Pro 2 공식 사용자 설명서](https://smartcara.com/article/%EC%A0%9C%ED%92%88-%EB%A7%A4%EB%89%B4%EC%96%BC/5/46619/) |
| `P-S03` | 공식 사실 · `fact` | 필터 호환과 교체 관련 공식 정보 | URL 확인, 원문 추출 전 | [공식 필터·건조통 안내](https://smartcara.com/article/%EA%B3%B5%EC%A7%80%EC%82%AC%ED%95%AD/1/46425/) |
| `P-S04` | 지역 행정 사실 · `fact` | 2026년 서초구 대상·기간·지원 범위·마감 상태 | 본문 확인, locator 고정 전 | [서초구 2026 소형감량기 지원사업](https://www.seocho.go.kr/site/seocho/ex/bbs/View.do?bcIdx=409216&cbIdx=57) |
| `P-S05` | 공식 안내 · `fact` | 지자체별 대상 모델·서류·금액이 다르다는 제한 | 본문 확인, locator 고정 전 | [스마트카라 보조금 FAQ](https://smartcara.com/article/%EC%9E%90%EC%A3%BC-%EB%AC%BB%EB%8A%94-%EC%A7%88%EB%AC%B8/6/46424/) |
| `P-A01` | 시청자 관측 · `audience` | 공식 FAQ·공개 사용후기의 냄새, 소음, 필터, 용량, 관리 질문 | materialize 전 | 공식 FAQ·사용후기 영역 |
| `P-R01` | 크리에이티브 패턴 · `creative` | 카탈로그의 두 모델 비교표와 구매 전 checklist 구조 | pattern만 허용 | `P-S01`의 layout 별도 card |
| `P-V01` | 시장 관측 · `market` | `음식물처리기`, `자취`, `꿀템` 관련 최대 5개 관측 | `provider_not_called` | Vira read-only snapshot |

서초구 source는 `2026-07-24` 현재 신청 마감 공지이며, 당시 공지의 “구매비 30% 범위
내 최대 21만 원”을 전국 공통 혜택처럼 말할 수 없다.

#### 고정 audience question set

1. 2 L가 우리 집의 하루 음식물 양에 충분한가?
2. 한 번 처리하는 데 실제로 어느 정도 시간을 잡아야 하는가?
3. 처리 중 냄새는 어떤 조건에서 달라질 수 있는가?
4. 밤에 사용할 때 소음이 생활에 영향을 주는가?
5. 필터는 언제 확인하고 어떤 비용을 예상해야 하는가?
6. 넣으면 안 되는 음식물이나 재료는 무엇인가?
7. 처리 중 추가 투입이 가능한가?
8. 세척과 건조통 관리는 얼마나 자주 필요한가?
9. 설치 공간, 환기, 전원에서 무엇을 확인해야 하는가?
10. 내 거주지의 보조금 대상·기간·서류는 어디에서 확인해야 하는가?

#### 필요한 시각 증거

- `용량 → 처리시간 → 필터 → 투입 제한 → 지역 지원` 순서의 구매 전 checklist
- 2 L 용량을 추상 아이콘이 아니라 공식 규격과 일상 사용 질문으로 연결한 화면
- 보조금은 지역명·공고일·마감 상태가 동시에 보이는 source card

### 4.3 IDOL-01 — LE SSERAFIM `CELEBRATION`

#### 운영 프로필

- 운영자: 공식 계정이 아닌 K-pop 콘텐츠 해설 채널
- 시청자: 노래와 MV를 봤지만 이번 활동의 공식 메시지와 표현 연결을 짧게 이해하고 싶은
  팬·일반 시청자
- 목표 행동: 공식 MV와 앨범 콘텐츠를 다시 보며 장면과 메시지 연결을 확인한다.
- 톤: 팬 친화적이되 사실, 매체 해석, AI 해석을 화면에서 구분한다.
- 금지: 멤버의 사생활·건강 상태 추정, 확인되지 않은 서사, 편집 해석을 아티스트의 직접
  발언으로 표시하는 행위

#### 고정 질문

- episode A: 공식 설명의 “변화를 받아들이고 앞으로 나아가는 순간을 축하한다”는
  메시지가 공식 콘텐츠에서 어떻게 표현되는가?
- episode B: `CELEBRATION`과 `BOOMPALA`는 두려움을 받아들이고 놓아주는 과정을 각각
  어떻게 다르게 표현하는가?

#### source inventory

| ID | 분류와 허용 용도 | 이번 검증에서 추출할 것 | 현재 상태 | 원문 |
|---|---|---|---|---|
| `I-S01` | 공식 사실 · `fact` | 앨범·곡 발매 시점과 Source Music이 밝힌 핵심 메시지 | 본문 확인, locator 고정 전 | [Source Music Weverse release notice](https://weverse.io/lesserafim/notice/34880) |
| `I-S02` | 공식 콘텐츠 · `fact` | 메시지를 검토할 장면·행동·편집의 timestamp | URL 확인, timestamp annotation 전 | [CELEBRATION official MV](https://www.youtube.com/watch?v=a2grcJdfXmY) |
| `I-S03` | 아티스트 발언 · `fact` | 멤버가 직접 설명한 곡의 의미와 권장 청취 맥락 | 본문 확인, locator 고정 전 | [Weverse Magazine playlist](https://magazine.weverse.io/article/view/1874?artist=LE+SSERAFIM) |
| `I-E01` | 편집 해석 · `editorial_interpretation` | MV의 creature, 연대, 축하에 관한 매체 분석 | 본문 확인, 공식 발언으로 사용 금지 | [Weverse Magazine creature anthem](https://magazine.weverse.io/article/view/1881?artist=LE+SSERAFIM&lang=en) |
| `I-A01` | 시청자 관측 · `audience` | 공식 MV·Weverse 공개 반응에서 반복 질문을 비식별 집계 | materialize 전 | `I-S01`, `I-S02`의 공개 반응 |
| `I-R01` | 크리에이티브 패턴 · `creative` | 장면 timestamp → 공식 문장 → 해석을 3단으로 보여주는 annotation | pattern card 작성 전 | `I-S02`를 reference로만 사용 |
| `I-V01` | 시장 관측 · `market` | 공식 video 관측과 peer growth 중 최대 5개 | `provider_not_called` | Vira read-only snapshot |

공식 MV와 공식 사진은 근거 source이지 자동으로 재사용 가능한 production asset이 아니다.
실험 storyboard는 필요한 장면의 의도와 timestamp만 기록하며, 사용 권리는 별도로
확인한다.

#### 고정 audience question set

1. 이번 곡에서 무엇을 축하한다는 뜻인가?
2. “두려움이 없다”에서 “두려움을 받아들인다”로 무엇이 달라졌는가?
3. 공식 notice의 변화와 성장 메시지는 MV의 어느 장면과 연결되는가?
4. creature는 공식 설명인가, 매체의 해석인가, 영상에서 관찰한 상징인가?
5. “Fearless 2.0”은 멤버가 직접 어떻게 설명했는가?
6. 축제 같은 사운드와 불확실한 정서가 함께 느껴지는 이유는 무엇인가?
7. 공식 MV에서 반복되는 이동·만남·춤은 어떤 전개를 만드는가?
8. 팬이 놓치기 쉬운 공식 source는 무엇인가?
9. 매체 해석과 AI의 추가 해석을 어떻게 구분해서 봐야 하는가?
10. 다음 곡 `BOOMPALA`와 연결하면 메시지가 어떻게 확장되는가?

#### 필요한 시각 증거

- 공식 문장, MV timestamp 관찰, 편집 해석을 색과 label로 분리한 3단 card
- 전체 클립 나열이 아니라 질문에 답하는 3~4개 장면만 고른 timeline
- 얼굴 생성이나 실제 장면 합성을 기본값으로 사용하지 않는다.

### 4.4 EXPERT-01 — 채권 가격과 시장금리

#### 운영 프로필

- 운영자: 금융 입문 교육 채널
- 시청자: 예금 금리와 채권 금리를 같은 방식으로 이해해 가격 변동이 낯선 입문자
- 목표 행동: 기존 고정 coupon 채권과 새 채권의 상대적 매력을 숫자로 설명할 수 있다.
- 톤: 수식보다 비교와 도식이 먼저이며, 단순화한 조건을 명시한다.
- 금지: 개인화 투자 조언, 현재 금리 예측, 채권 가격이 금리 하나로만 결정된다는 표현

#### 고정 질문

- episode A: 시장금리가 3%에서 4%로 오르면 기존 3% 고정금리 채권의 가격은 왜
  내려가는가?
- episode B: 같은 신용위험과 coupon 조건이라면 만기가 긴 채권이 금리 변화에 더 민감한
  이유는 무엇인가?

#### source inventory

| ID | 분류와 허용 용도 | 이번 검증에서 추출할 것 | 현재 상태 | 원문 |
|---|---|---|---|---|
| `E-S01` | 권위 설명 · `fact` | 국내 채권시장 기본 구조와 가격·금리 관계 설명 위치 | 본문 확인, episode locator 고정 전 | [한국은행 우리나라 채권시장의 이해와 최근 동향](https://www.bok.or.kr/portal/bbs/B0000217/view.do?menuNo=200144&nttId=10073634) |
| `E-S02` | 규제기관 교육 · `fact` | 3% 기존 채권과 4% 새 채권 예시, 가격·금리 역관계, 만기 보유 조건 | 본문 확인, locator 고정 전 | [SEC Investor.gov: What Are Corporate Bonds?](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins/what-are) |
| `E-S03` | 자율규제기관 교육 · `fact` | 가격·금리의 반대 방향, discount 설명, duration risk | 본문 확인, locator 고정 전 | [FINRA: Bonds](https://www.finra.org/investors/investing/investment-products/bonds) |
| `E-A01` | 시청자 관측 · `audience` | 입문 교육 댓글·질문에서 coupon, yield, 만기 보유 오해를 비식별 요약 | materialize 전 | 교육 source의 공개 질문과 별도 공개 Q&A |
| `E-R01` | 크리에이티브 패턴 · `creative` | 숫자를 한 단계씩 바꾸는 whiteboard 설명 순서 | pattern만 허용 | [Khan Academy 설명 형식](https://www.khanacademy.org/v/relationship-between-bond-prices-and-interest-rates?playlist=Finance) |
| `E-V01` | 시장 관측 · `market` | `재테크`, `채권`의 framing·format 관측만 최대 5개 | `provider_not_called` | Vira read-only snapshot |

`E-V01`은 의도적인 negative-control 성격을 가진다. Vira 관측이 약하면 약한 상태를
유지하고, 채권의 사실 근거나 현재 투자 판단을 보충하기 위해 사용하지 않는다.

#### 고정 audience question set

1. coupon 3%와 시장금리 4%는 무엇이 다른가?
2. 기존 채권의 이자가 그대로인데 왜 가격이 변하는가?
3. 새 채권이 더 높은 이자를 주면 기존 채권을 누가 사는가?
4. 가격이 얼마나 내려가야 두 채권의 매력이 비슷해지는가?
5. 만기까지 보유하면 중간 가격 하락은 왜 다르게 봐야 하는가?
6. 가격과 yield가 반대로 움직인다는 말은 무슨 뜻인가?
7. 기준금리와 모든 시장금리는 항상 같은 폭으로 움직이는가?
8. 만기가 길수록 금리 변화에 민감한 이유는 무엇인가?
9. 신용위험과 금리위험은 어떻게 다른가?
10. 이 설명에서 단순화를 위해 같다고 가정한 조건은 무엇인가?

#### 필요한 시각 증거

- 기존 3% 채권과 새 4% 채권의 현금흐름을 나란히 놓는 비교
- `시장금리 ↑ / 기존 채권 가격 ↓`를 보여주는 seesaw
- 만기 보유와 중도 매각을 분리한 timeline
- 숫자 예시는 신용위험·만기 등 다른 조건이 같다는 가정을 화면에 표시한다.

## 5. 입력 조합 비교 실험

### 5.1 공통 통제 조건

실제 provider 실행 전에 하나의 run manifest에 다음 값을 기록하고 모든 조건에서
고정한다.

- provider와 model의 정확한 version
- system prompt와 output schema revision
- temperature, seed 지원 여부, token 상한
- 언어와 45초 목표 길이
- source pack digest와 cutoff
- 실행 시각, condition ID, 실패·재시도 기록

탐색 run에서는 seed를 지원하면 모든 조건에 같은 seed를 사용한다. 입력 축을
기본값·조건부·제외로 최종 분류하기 전에는 판단 근거가 된 핵심 비교 pair를 3회
확인한다. seed 지원 시에는 사전 등록한 서로 다른 3개 seed, 미지원 시에는 3개의 독립
표본을 사용하고 중앙값을 비교한다. provider 오류로 재시도한 결과를 조용히 교체하지
않고 모두 기록한다.

### 5.2 두 개의 출력 track

각 condition package는 서로 독립된 두 호출로 평가한다.

조건에 source가 없을 때 evidence 필드는 `none_available`로 명시한다. 모델의 기억을
source ID처럼 꾸미거나 존재하지 않는 근거를 채우게 하지 않는다.

#### Track D — opportunity discovery

동일 입력에서 서로 다른 Content Opportunity 3개를 생성한다.

각 opportunity의 필수 항목:

- 한 문장 thesis
- 대상 시청자의 질문 또는 tension
- hook
- 새로 알게 될 payoff
- 핵심 evidence ID
- visual proof idea
- 이번 조건에서 만들 수 없는 주장

#### Track E — locked opportunity elaboration

표 1의 고정 episode 질문을 바꾸지 않고 다음 산출물을 생성한다.

- Director Brief
- 약 45초 대본
- 5~7개 beat storyboard
- beat별 claim과 evidence ID
- visual/asset intent와 fallback
- uncertainty·rights·safety note

Track D는 “좋은 주제를 찾는가”, Track E는 “같은 주제를 더 잘 구체화하는가”를 분리한다.
Track D에서 고른 기회를 Track E에 넘기지 않아 선택 운이 비교에 섞이지 않게 한다.

### 5.3 1단계 — 누적 입력 ladder

episode A는 다음 여섯 조건으로 실행한다.

| 조건 | 포함 입력 | 목적 |
|---|---|---|
| `C0` | episode prompt | 현재 prompt-only 기준선 |
| `C1` | `C0 + P` | profile의 순효과 탐색 |
| `C2` | `C1 + S` | 공식 source의 추가 효과 탐색 |
| `C3` | `C2 + A` | audience 질문의 추가 효과 탐색 |
| `C4` | `C3 + V` | Vira snapshot의 추가 효과 탐색 |
| `C5` | `C4 + R` | creative pattern의 추가 효과 탐색 |

그 뒤 episode A의 `C5` 결과에 대해 편집자가 승인·수정·실패 이유를 기록해 최대 3개의
feedback card를 만든다. episode B에는 모든 입력과 feedback을 포함한 `C6`을 적용한다.

| 조건 | 포함 입력 | 목적 |
|---|---|---|
| `C6` | episode B + `P + S + A + V + R + F` | 과거 피드백의 자매 episode 전이 탐색 |

기본 ladder는 `4개 사례 × 7개 조건 = 28 condition package`다. 각 package가 Track D와
Track E를 별도 생성하므로 1회 표본 기준 생성 호출은 56회다. seed 미지원 시 실시하는
핵심 pair 반복 호출은 이 수에 별도로 더한다.

### 5.4 2단계 — 순서 효과를 줄이는 targeted ablation

누적 ladder만으로는 뒤에 추가한 입력이 유리하거나 앞 입력과 겹치는 순서 효과를 완전히
분리할 수 없다. 따라서 다음 제거 실험을 실시한다.

#### feedback 필수 대조군

각 episode B를 feedback 없이 `P + S + A + V + R`로 한 번 더 실행한다. 같은 episode B의
`F 없음`과 `F 있음`을 비교하므로 feedback을 같은 결과 재작성 능력이 아닌 전이 능력으로
평가할 수 있다.

이 필수 대조군은 4 condition package, Track D·E 합계 8회 호출이다. 따라서 1회 표본
기준 최소 실험은 총 32 package, 64회 생성 호출이다.

#### 다른 축의 선택적 대조군

episode A의 full input인 `P + S + A + V + R`에서 한 축만 제거한다.

```text
FULL-P
FULL-S
FULL-A
FULL-V
FULL-R
```

다음 중 하나를 만족한 축만 해당 사례에서 실행한다.

- ladder에서 목표 차원 점수가 `0.5`점 이상 변했다.
- hard fail의 발생 또는 제거와 연결됐다.
- 평가자 간 점수 차이가 `2`점 이상이다.
- 새 입력 뒤 사실 정확성 또는 제작 가능성이 오히려 낮아졌다.

선택 규칙을 실행 결과를 본 뒤 바꾸지 않는다. 어떤 ablation이 왜 선택됐는지 run
manifest에 남긴다.

### 5.5 blind evaluation

- 출력에서 case ID, condition ID와 source pack 크기를 숨기고 무작위 blind ID를
  부여한다.
- 1차 평가는 source를 보지 않는 creative quality pass다. evidence ID는 의미가 드러나지
  않는 중립 token으로 치환한다.
- 2차 평가는 source pack을 열어 claim-evidence를 확인하는 evidence audit다.
- 실제 실험은 최소 2명의 평가자가 독립 채점한다.
- 같은 차원에서 2점 이상 차이나거나 hard fail 판단이 다르면 source locator를 보며
  조정한다.
- 생성 모델 자신의 self-score는 진단 로그로만 보관하고 최종 점수에 넣지 않는다.

## 6. 평가 rubric

### 6.1 가중치

| 차원 | 가중치 | 주 평가 대상 |
|---|---:|---|
| 구체성 | 15% | D, E |
| 새로움 | 10% | D 중심 |
| 시청자 관련성 | 15% | D, E |
| 근거 정확성 | 20% | E 중심 |
| hook-payoff | 15% | D, E |
| 시각화 가능성 | 15% | E 중심 |
| 제작 가능성 | 10% | E |

가중 총점은 `Σ(차원 점수 × 가중치)`로 계산하며 범위는 1.0~5.0이다. Track D의 세
opportunity는 각각 채점한 뒤 차원별 중앙값을 package 점수로 사용하고, Track E는 단일
산출물을 채점한다. D와 E는 하나의 총점으로 합치지 않고 나란히 보고한다. 입력이 기회
발견과 구체화에 서로 다른 영향을 줄 수 있기 때문이다. hard fail이 있는 개별 산출물은
총점과 관계없이 채택 후보에서 제외하고 package별 hard fail 수도 함께 기록한다.

### 6.2 1·3·5점 anchor

| 차원 | 1점 | 3점 | 5점 |
|---|---|---|---|
| 구체성 | 어느 주제에도 붙일 수 있는 일반론 | 일부 구체 정보가 있으나 thesis·beat 연결이 약함 | thesis, claim, beat가 이 사례의 source와 조건에 구체적으로 묶임 |
| 새로움 | 익숙한 목록이나 홍보 문구 반복 | 하나의 의미 있는 각도가 있으나 예상 가능함 | evidence에 근거한 비자명한 관점이 있고 과장하지 않음 |
| 시청자 관련성 | 대상의 질문·상태와 무관함 | 넓은 관심사는 맞지만 실제 선택이나 오해와 거리가 있음 | 반복 질문과 현재 상태를 정확히 짚고 원하는 after-state로 이동시킴 |
| 근거 정확성 | 핵심 주장이 무근거·왜곡·출처 혼합 | 핵심은 대체로 지지되지만 label·시점·불확실성 표시가 약함 | 모든 핵심 claim이 evidence ID·locator와 연결되고 계층·시점·한계를 정확히 표시 |
| hook-payoff | clickbait이거나 끝에서 답하지 않음 | hook과 답은 연결되지만 모호하거나 payoff가 약함 | 구체적 open loop를 만들고 마지막에 evidence로 분명히 회수함 |
| 시각화 가능성 | 검색 이미지 슬라이드로만 구성 | 몇 개 beat는 설명 기능이 있으나 장식 화면이 남음 | 각 beat의 visual이 설명·비교·증명의 역할을 가지며 fallback도 있음 |
| 제작 가능성 | 권리·asset·현 renderer 제약 때문에 실행 불가 | 대체 asset이나 수작업 보완이 필요함 | 현재 제약 안에서 만들 수 있고 unavailable 시 fallback이 명시됨 |

### 6.3 hard fail

다음 중 하나라도 있으면 무효다.

- 핵심 사실 claim이 source와 모순되거나 source 없이 단정됨
- Vira 수치, source, quote 또는 관측을 만들어 냄
- 상관관계를 인과관계로 바꿈
- 공식 사실, 시청자 반응, 편집 해석, AI 가설을 구분하지 않음
- 개인정보, 사생활 추정, 안전·규제·금융 조언 경계를 위반함
- payoff가 권리상 사용할 수 없는 asset 하나에만 의존하고 fallback이 없음

### 6.4 품질 외 운영 지표

각 조건은 다음 값을 함께 기록한다.

| 지표 | 단위 |
|---|---|
| profile 작성 부담 | 사용자 분 |
| source 선별 부담 | 운영자 분 |
| audience 정리 부담 | 운영자 분 |
| input / output token | token |
| provider 비용 | 실제 과금 단위 |
| provider latency | 초 |
| source·Vira 부족 | source 수와 상태 |
| schema 실패·재시도 | 횟수 |

## 7. 입력 축 유지·조건부·제외 판정

한 번의 최고 점수가 아니라 사례 간 재현성과 비용을 함께 본다.

### 7.1 기본 입력 후보

다음 조건을 모두 만족하면 기본 입력 후보로 둔다.

- 관련 목표 차원에서 2개 이상 사례의 평균 또는 중앙값이 `0.5`점 이상 상승하거나,
  반복되는 hard fail을 제거한다.
- evidence 정확성이나 제작 가능성을 악화시키지 않는다.
- 비용과 사용자 부담을 줄이는 합리적인 기본값 또는 자동 수집 경로가 있다.

### 7.2 조건부 입력

다음이면 route·사례별 조건부 입력으로 둔다.

- 한 운영 경로에서만 분명한 이득이 있다.
- 충분한 source나 Vira 관측이 있을 때만 이득이 있다.
- 품질 이득은 있으나 권리 확인이나 사람의 검토 비용이 높다.

### 7.3 기본값에서 제외

다음이면 기본 흐름에서 제외한다.

- 목표 차원 개선이 `0.25`점 미만인데 사용자·token 부담이 유의미하다.
- 다른 입력과 중복돼 제거 ablation에서도 차이가 없다.
- 근거 계층 혼합, 허위 구체성, 제작 불가능성을 반복적으로 증가시킨다.

제외는 기능 삭제를 뜻하지 않는다. 향후 수동 고급 입력으로 남길 수 있다.

### 7.4 해석 한계

이 실험은 네 실제 사례에서 제품 기본값을 결정하기 위한 설계 검증이지 통계적 인과
추정을 위한 대규모 연구가 아니다.

- 사례 간 점수보다 같은 사례 안의 condition 차이를 우선한다.
- 4개 사례 밖의 모든 업종으로 결과를 일반화하지 않는다.
- rubric 점수는 실제 게시 후 retention, completion, save, comment 성과를 대체하지
  않는다.
- renderer 품질과 asset 획득 성공률은 이번 점수의 직접 검증 범위가 아니다.
- `0.5`와 `0.25` 기준은 이번 검증의 의사결정선이며 보편적 품질 법칙이 아니다.

## 8. feedback card 계약

feedback은 자유문장 transcript 전체가 아니라 다음 구조의 card로 압축한다.

```text
feedback_id
source_output_blind_id
decision: approve | revise | reject
applies_to: hook | thesis | claim | evidence | visual | feasibility | tone
observed_problem
preferred_rule
evidence_or_example
scope: route | topic_family | global
```

한 사례에서 episode A feedback card는 최대 3개다. episode B 결과가 좋아졌더라도 source나
질문 차이로 설명될 수 있으면 feedback 효과로 인정하지 않는다. 같은 episode B의
feedback 없는 대조군과 비교해야 한다.

## 9. 실행 전 materialization gate

다음이 모두 충족되기 전에는 생성 provider 실험을 시작하지 않는다.

1. 네 case pack의 source 원문 또는 허용된 extract가 로컬 artifact로 동결됨
2. 각 핵심 claim에 evidence locator가 있음
3. 모든 artifact에 digest, cutoff와 rights note가 있음
4. audience 질문이 비식별 처리되고 원문 계정 정보가 제거됨
5. `V` 축을 실행한다면 승인된 대표 corpus가 별도로 materialize되고 관측 coverage가
   기록됨. 현재 Vira 테스트 DB의 `provider_not_called` pack은 `insufficient`로
   재해석하지 않으며 Vira 의존 condition을 실행하지 않음
6. provider·model·prompt·schema·sampling 값이 run manifest에 고정됨
7. blind ID와 두 평가자용 score sheet가 준비됨

Vira를 실제로 조회할 때도 저장·수정 없이 read-only로 사용한다. Vira DB/API/provider
호출과 생성 provider 호출은 각각 실행 전에 사용자에게 알린다.

## 10. 현재 완료 범위와 다음 검토점

2026-07-24 세션에 완료한 것은 다음과 같다.

- 서로 다른 운영 경로의 실제 사례 4개 선택
- 사례별 episode A·B와 운영 프로필 고정
- 공개 source inventory를 실제 artifact로 materialize하고 digest·locator와 함께 seal
- audience 질문 10개씩 정의
- Vira offline fixture, read-only wrapper와 normalizer 계약 검증
- 네 실제 case의 Vira 상태를 `provider_not_called`, 빈 evidence로 보존
- 누적 ladder, feedback 대조군, targeted ablation 정의
- blind two-pass 평가와 7차원 rubric 정의
- 전체 offline test 38/38 통과와 독립 spec/quality review 승인

아직 실행하지 않은 것은 다음과 같다.

- 대표 YouTube Shorts corpus의 수집 전략 결정
- Vira feature branch 또는 독립 collector 선택
- 최근 keyword discovery, coverage gate와 반복 snapshot
- 실제 `V` evidence materialization
- 실제 생성 provider 호출
- 사람 평가와 결과 분석
- production 코드·목업·DB·API 변경

다음 세션에서는 기존 실행 계획의 live Vira read로 진행하지 않는다. corpus options를
검토하고 사용자가 목적과 접근을 승인한 뒤 별도 설계·작업 계획을 만든다.
