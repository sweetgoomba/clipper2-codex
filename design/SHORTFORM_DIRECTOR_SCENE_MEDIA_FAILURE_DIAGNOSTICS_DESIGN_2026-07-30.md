# AI 숏폼 디렉터 장면 미디어 결정 실패 보완 설계

날짜: 2026-07-30

## 1. 확인된 문제

영상 후보를 제작안으로 바꾸는 실행에서 첫 번째 `video-plan` OpenAI 호출은 성공했지만,
두 번째 `scene-media-decision` 호출이 Web API 502로 실패했다.

현재 로컬 실패 산출물은 `stage=scene-media-decision`, `category=provider`만 저장한다.
Web API가 이미 안전하게 정리해 반환하는 오류 코드, HTTP 상태, 검증 실패 위치와 토큰 사용량도
버리기 때문에 실행 종료 후에는 provider HTTP 오류와 출력 스키마 오류를 구분할 수 없다.

또한 `scene-media-decision`의 수동 검증기는 다음 조건을 강제하지만 현재 LLM 지시문은 이를
완전하게 설명하지 않는다.

- 입력 영상 계획의 모든 장면에 정확히 하나의 결정을 반환한다.
- `official-source` 및 고위험 사실 장면은 실제 `productionSourceId`를 사용한다.
- `image-search`에는 `searchBrief`가 필요하다.
- `generated-image`와 `generated-video`에는 `generationBrief`가 필요하다.
- 결과의 evidence/source 식별자는 입력에 제공된 식별자만 사용한다.

## 2. 승인된 변경

### 2.1 Web API 지시문 정합성

`scene-media-decision` 지시문을 실제 검증 규칙과 맞춘다.
프롬프트가 바뀌므로 해당 목적의 `promptTemplateVersion`만 v2로 올린다.
모델, provider, 응답 스키마와 호출 횟수는 바꾸지 않는다.

### 2.2 로컬 실패 진단 JSON

`WebApiProviderError.responseBody` 전체를 저장하지 않는다. 다음 필드만 별도 projector로
허용 목록 투영해 `candidate-production-failure` 산출물에 추가한다.

- Web API 오류 코드
- Web API HTTP 상태와 upstream provider 상태
- 출력 검증 실패의 `path`와 `keyword`
- 입력·출력·추론 토큰 수
- provider 지연 시간

프롬프트, 사용자 입력, provider 원문, 파싱된 출력, 응답 body, 인증값, 예외·스택은 저장하지
않는다. 문자열·배열 개수와 숫자 범위를 제한하며 예상 형태가 아니면 진단 필드를 생략한다.

### 2.3 호출 및 비용 계약

자동 재시도는 추가하지 않는다. 영상 기획 실행은 계속 최대 두 번만 외부 호출한다.
따라서 기존 `candidate-production` 승인 버전, 최대 호출 수와 예상 비용은 바꾸지 않는다.

## 3. 테스트

- Web API: `scene-media-decision` 지시문이 모든 조건과 v2 버전을 포함하는 회귀 테스트
- Desktop Nest: Web API 실패 응답에서 허용된 진단만 투영하고 원문·프롬프트·인증값은
  저장하지 않는 회귀 테스트
- 기존 inference, 후보 제작, artifact security 테스트 전체 회귀

## 4. 완료 기준

1. 같은 제작 요청에서 장면 미디어 결정이 검증 규칙을 만족할 가능성을 높인다.
2. 다시 실패해도 추가 유료 진단 호출 없이 로컬 JSON만으로 오류 종류와 검증 위치를 확인한다.
3. 자동 재시도나 숨겨진 추가 비용이 없다.
