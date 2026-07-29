# AI 숏폼 디렉터 실제 Shorts 발견 및 선택적 정밀 분석 설계

- 작성일: 2026-07-29
- 상태: 사용자 방향 승인, 구현 전 설계 고정
- 대상:
  - `desktop/clipper_nestjs`
  - `desktop/clipper_angular`
  - `web/clipper_web_api`
- 관련 기존 계약:
  - 최근 30일 조사
  - YouTube 조회수순·관련도순 2개 검색 lane
  - 로컬 JSON artifact·run manifest 저장
  - 유료 호출 전 실제 credential·모델·최대 호출·예상 비용 승인

## 1. 결정

YouTube 검색어에는 `shorts`, `쇼츠`, `챌린지` 같은 문자열을 강제로
추가하지 않는다. 이 문자열이 제목·설명·해시태그에 없는 실제 Shorts를
놓칠 수 있기 때문이다.

대신 다음 절차로 실제 Shorts를 판별한다.

1. LLM이 운영 프로필과 선택적 집중 키워드에 맞는 주제 검색어를 만든다.
2. 같은 검색어로 조회수순 40개와 관련도순 40개를 요청한다.
3. 두 요청 모두 조사 실행 시각 기준 최근 30일과
   `videoDuration=short`를 적용한다.
4. 최대 80개 검색 결과를 video ID로 중복 제거한다.
5. 중복 제거된 결과를 일부에서 중단하지 않고 전부
   `https://www.youtube.com/shorts/{videoId}`로 확인한다.
6. 실제 Shorts로 확인된 영상만 상세 메타데이터를 수집한다.
7. 실제 Shorts를 임의의 표시 개수로 자르지 않고 전부 저장하고 보여준다.
8. 사용자는 1~5개를 골라 정밀 분석하거나, 명시적으로 정밀 분석을
   건너뛸 수 있다.

`3분 이하` 또는 `4분 미만`은 최종 Shorts 판정 기준으로 사용하지 않는다.
`videoDuration=short`는 4분 이상 영상을 검색 단계에서 줄이는 사전
필터일 뿐이며, 최종 판정은 Shorts URL 응답으로 한다.

## 2. 검색 및 기간 계약

두 YouTube 검색 요청은 `order`를 제외하고 동일하다.

```json
{
  "q": "LLM이 생성한 주제 검색어",
  "publishedAfter": "조사 실행 시각에서 정확히 30일 전",
  "regionCode": "KR",
  "relevanceLanguage": "ko",
  "videoDuration": "short",
  "maxResults": 40
}
```

- 첫 요청: `order=viewCount`
- 둘째 요청: `order=relevance`
- 검색 API 호출 횟수: 2회 유지
- 검색 결과 최대치: 80개
- 중복 제거 후 최대치: 80개
- API 응답 후에도 `publishedAt`을 다시 검사하여 30일 범위 밖 결과를
  허용하지 않는다.
- 검색 API가 반환한 모든 결과와 실제 요청 파라미터는 기존 source-call
  artifact에 저장한다.

## 3. 실제 Shorts 판별

### 3.1 요청

중복 제거된 모든 video ID에 대해 서버 측 GET 요청을 보낸다.

```text
GET https://www.youtube.com/shorts/{videoId}
redirect: manual
```

HEAD가 아니라 GET을 사용하며 응답 본문은 저장하지 않는다. 동시 요청은
8개로 제한하고, 각 요청에는 10초 timeout을 적용한다. 일시적 네트워크
오류 또는 5xx에는 최대 1회만 재시도한다.

### 3.2 판정

- `200`, redirect 없음: `shorts`
- `301`, `302`, `303`, `307`, `308`이고 같은 video ID의
  `/watch?v={videoId}`로 이동: `not-shorts`
- timeout, 네트워크 오류, 예상하지 않은 상태·위치: `unverified`

`unverified`를 일반 영상 또는 Shorts로 임의 판정하지 않는다. 모든
결과는 검사를 시도하지만 검증되지 않은 영상은 실제 Shorts 후보에는
포함하지 않고 화면에서 별도 개수와 재시도 가능 상태로 알린다.

### 3.3 저장

본문 HTML, cookie, 전체 header, 인증값은 저장하지 않는다. 하나의
`shortform-director-youtube-shorts-validation.v1` JSON artifact에 다음
allowlist만 저장한다.

```json
{
  "schemaVersion": "shortform-director-youtube-shorts-validation.v1",
  "runId": "run.director....",
  "query": "주제 검색어",
  "checkedAt": "ISO-8601",
  "results": [
    {
      "videoId": "MMpTTgXf2Ek",
      "searchLanes": ["current-relevant"],
      "sourceArtifactIds": ["artifact.director...."],
      "requestedUrl": "https://www.youtube.com/shorts/MMpTTgXf2Ek",
      "attemptCount": 1,
      "status": 200,
      "redirectLocation": null,
      "outcome": "shorts"
    }
  ]
}
```

근거 화면에서는 전체 JSON을 기본으로 접어 두고 다음 내용을 사람이
읽기 쉬운 표로 먼저 보여준다.

- 검색 결과 수
- 중복 제거 후 검사 대상 수
- 실제 Shorts 수
- 일반 영상 수
- 검증 실패 수
- 영상별 판정과 근거 상태

## 4. 상세 메타데이터와 후보 표시

Shorts URL로 확인된 모든 video ID를 `videos.list`로 조회한다. 현재 앱
계약의 batch당 최대 50개를 지키기 위해 최대 두 번으로 나눈다.

저장·표시 대상:

- 제목과 설명
- 채널
- 썸네일
- 게시 시각
- 길이
- 조회수·좋아요·댓글
- 시간당 조회수
- 참여율
- 조회수순·관련도순 lane
- 검색 source artifact
- Shorts 판별 artifact
- 기존 결정적 rank score와 설명

후보 목록은 rank score 순으로 정렬하되 최대 6개 같은 표시 제한을 두지
않는다. 같은 채널 영상이 많다는 이유로 저장 또는 표시에서 제거하지
않는다. 정렬과 점수는 사용자의 선택을 돕는 정보일 뿐 자동 선택으로
사용하지 않는다.

기존 `recommendedVideoIds`는 하위 호환 읽기에는 유지할 수 있지만 새
화면의 기본 선택을 만들지 않는다. 새 조사 결과의 선택 초기값은 항상
빈 배열이다.

## 5. 정밀 분석 선택

### 5.1 선택 규칙

- 선택 전: 0개
- 분석 실행 가능: 1~5개
- 최대: 5개
- 중복 또는 현재 후보에 없는 video ID: 거부
- 6개 이상: 거부
- 후보를 선택하는 것만으로 유료 호출하지 않는다.

화면에는 다음 두 동작을 분리한다.

1. `선택한 N개 정밀 분석`
2. `정밀 분석 없이 계속`

0개 선택은 아직 고르는 중인 상태와 구분할 수 없으므로 자동으로
건너뛰지 않는다. 두 번째 버튼을 눌러야만 명시적 skip으로 기록한다.

### 5.2 선택 분석 preflight

1~5개를 선택하면 현재 구조대로 실제 credential과 모델을 읽어 다음을
선택 개수에 맞춰 동적으로 계산한다.

- YouTube 댓글: 선택 영상당 최대 1회
- 로컬 STT: 선택 영상당 1회, 외부 STT 비용 없음
- Gemini 실제 영상 분석: 재사용되지 않는 선택 영상당 기본 1회,
  영상당 최대 1회 재시도
- OpenAI reference-pattern synthesis: 기본 1회, 최대 1회 재시도
- OpenAI topic synthesis: 기본 1회, 최대 1회 재시도

사용자가 화면에서 비용을 승인한 뒤에만 실행한다.

### 5.3 명시적 skip preflight

정밀 분석을 건너뛰면 YouTube 댓글, 로컬 STT, Gemini 영상 분석,
reference-pattern synthesis는 실행하지 않는다.

시장 근거만 사용하는 topic synthesis OpenAI 호출은 남으므로, skip
버튼 뒤에도 그 한 호출의 모델·credential·최대 호출·예상 비용을
보여주고 별도 승인을 받는다.

승인된 skip은 다음 artifact로 저장한다.

```json
{
  "schemaVersion": "shortform-director-reference-analysis-skip.v1",
  "runId": "run.director....",
  "candidateSnapshotId": "reference-candidates....",
  "decision": "user-skipped",
  "decidedAt": "ISO-8601"
}
```

## 6. 후속 품질 경로

시장 조사와 영상 정밀 분석의 역할은 분리한다.

- 시장 조사: 지금 무엇을 말할지
- 영상 정밀 분석: 그것을 어떻게 보여줄지

정밀 분석 결과는 다음에 실제로 전달한다.

- hook formula
- scroll stopper
- 구간별 구조
- 장면·구도 전환
- pacing과 visual reset
- 화면 문구 사용법
- CTA
- 댓글 기반 audience signal
- 복제하면 안 되는 원본 표현

이 데이터는 reference-pattern synthesis를 거쳐 topic synthesis와 영상
후보 생성에 실제 내용으로 전달된다. 따라서 최종 영상의 훅, 구성,
편집 리듬 개선에 직접 기여한다.

skip 경로에서는 시장 근거만으로 주제와 영상 후보를 만든다.

- `audienceSignals=[]`
- `referencePatterns=[]`
- 생성된 topic의 `audienceSignalIds=[]`
- 생성된 topic의 `referencePatternIds=[]`

시장 근거 `evidenceIds`는 여전히 필수다. LLM schema와 서버 검증은
참고 분석 입력이 비었을 때만 두 배열이 비는 것을 허용한다. 참고
분석이 존재하는데 ID가 빠진 결과는 계속 거부한다.

후속 candidate generation도 topic에 참고 신호가 없으면 시장 근거만
필수로 사용하고, 존재하는 참고 신호를 누락하는 것은 허용하지 않는다.
이를 통해 skip은 동작하지만, 정밀 분석을 한 경로보다 형식·편집 근거가
적다는 사실은 UI에 명확히 표시한다.

## 7. 실행 상태와 복구

기존의 “정확히 3개 분석 성공” 조건을 제거한다.

- 선택 N개(1~5개)의 분석이 모두 성공하면 synthesis를 시작한다.
- 실행 중 앱이 종료돼도 선택 revision의 N개를 기준으로 복구한다.
- 현재 선택 revision과 다른 과거 분석 결과는 재사용하지 않는다.
- 같은 영상의 검증된 분석 artifact는 기존 규칙대로 재사용한다.
- 분석 실패는 숨기지 않고 영상별 재시도 또는 선택 변경을 제공한다.
- 사용자가 skip을 승인하면 분석 child run 없이 시장 근거 synthesis로
  전환한다.
- 아무 선택·skip도 없으면 `awaiting_reference_selection`에서 안전하게
  멈추며 비용이 발생하지 않는다.

## 8. 오류 처리

- 검색 lane 하나 실패: 성공한 lane의 전체 결과를 검사하고 run을
  `partial`로 표시한다.
- 두 검색 lane 모두 실패: 안전한 failure artifact를 남기고 실패한다.
- 일부 Shorts URL 검증 실패: 나머지를 계속 검사하고 `unverified`를
  별도로 표시한다.
- 상세 metadata에서 일부 video ID가 사라짐: 해당 영상만 제외하고
  결과 개수를 기록한다.
- 실제 Shorts 0개: 빈 후보 화면과 명시적 skip을 제공하며 502로 만들지
  않는다.
- 선택 분석 중 provider 실패: 기존 성공 artifact는 보존하고 실패한
  영상만 재시도할 수 있게 한다.

## 9. UI

아이디어 찾기 페이지의 참고 영상 영역은 다음을 보여준다.

- 최근 30일
- 조회수순 최대 40개
- 관련도순 최대 40개
- 중복 제거 수
- 전체 Shorts 검증 진행 상태
- 실제 Shorts 전체 목록
- 선택 `N/5`
- 선택한 영상의 합산 예상 비용으로 이동하는 분석 버튼
- `정밀 분석 없이 계속` 보조 버튼
- 영상별 `근거와 과정 보기`

목록은 모두 접근 가능해야 하며 데이터 자체를 6개로 자르지 않는다.
필요한 UI 렌더 최적화는 목록 데이터 누락과 분리한다.

## 10. 검증 기준

### 자동 검증

- 두 search 요청 모두 `maxResults=40`, 같은 30일 `publishedAfter`,
  `videoDuration=short`를 보낸다.
- 최대 80개에서 중복 제거된 모든 ID에 Shorts URL 확인을 시도한다.
- 200, watch redirect, timeout·예상 밖 응답을 각각 정확히 분류한다.
- 검증 raw HTML, cookie, 전체 header는 저장하지 않는다.
- 실제 Shorts 전체를 후보 snapshot에 보존한다.
- 선택 1개와 5개는 통과하고 0개 일반 분석 요청과 6개는 거부한다.
- skip은 별도 명시적 승인으로만 동작한다.
- 선택 개수에 따라 댓글·Gemini·로컬 STT 비용과 호출 수가 변한다.
- 선택 N개의 성공을 기준으로 재개·복구한다.
- 시장-only topic은 빈 audience/reference ID를 허용하되 시장 근거를
  반드시 요구한다.
- 기존 3개 선택 artifact와 완료 run은 계속 읽을 수 있다.

### 실제 E2E 검증

1. 운영 프로필과 집중 키워드로 discovery 승인
2. 실제 Google Trends·Naver·YouTube·OpenAI 호출
3. 두 YouTube lane에 최근 30일·40개 조건이 저장됐는지 확인
4. 중복 제거된 모든 결과의 Shorts URL 판정 JSON 확인
5. 실제 Shorts 전체가 화면에 보이는지 확인
6. 사용자가 1~5개 중 원하는 개수를 선택
7. 실제 비용 preflight 승인
8. 실제 미디어 획득·로컬 STT·Gemini 영상 분석
9. reference pattern과 topic 생성 확인
10. 이후 최소 10개 영상 후보 생성과 실제 영상 제작 흐름까지 진행

더미 provider 응답이나 fixture로 실제 E2E 완료를 주장하지 않는다.

## 11. 비목표

- YouTube 검색어에 `shorts` 또는 `쇼츠`를 강제 추가하지 않는다.
- Google Trends 페이지 스크래핑은 도입하지 않는다.
- Google Trends 공식 API 알파 승인 전에는 해당 API를 사용하지 않는다.
- 정밀 분석 영상을 자동 선택하거나 승인 없이 유료 호출하지 않는다.
- 표시 개수를 6개로 제한하지 않는다.
- 정밀 분석 개수를 정확히 3개로 고정하지 않는다.
- AI Director 크레딧 차감 기능을 다시 도입하지 않는다.
- Remotion을 도입하거나 대체 렌더러로 언급하지 않는다.
