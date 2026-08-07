# Shortform Director Nano Banana 2 이미지 제작 설계

Date: 2026-08-07
Status: 사용자 문서 검토 승인 완료

## 1. 목표

AI 숏폼 디렉터에 `Nano Banana 2` 이미지 제작 경로를 추가한다. 이 경로는
생성형 영상 대신 여러 장의 AI 생성 이미지를 컷별로 사용하고, 기존 Clipper TTS,
자막, 타이틀, 오디오, 템플릿, 렌더 큐를 그대로 사용해 최종 영상을 만든다.

```text
영상 후보
  → Nano Banana 2 선택
  → Clipper 템플릿 방식 고정
  → 스토리보드 생성
  → TTS와 실제 타임라인 확정
  → 이미지 컷별 비용 확인·승인·생성
  → 기본 1:1 템플릿으로 Clipper 최종 렌더
  → AI 숏폼 디렉터와 프로젝트 보관함에서 결과 확인
```

이번 변경은 기존 AI 영상 job에 이미지 상태를 억지로 추가하지 않는다. 별도의
AI 이미지 job을 만들고, 비용 승인·공급자 오류·로컬 영속화·최종 렌더 연결에서
검증된 기존 흐름을 재사용한다.

대상 저장소는 다음과 같다.

- `desktop/clipper_angular`
- `desktop/clipper_nestjs`
- `web/clipper_web_api`
- 크로스 저장소 설계 문서는 `clipper_docs`

Gemini 자격 증명은 기존 Google AI 자격 증명을 재사용하므로
`web/clipper_web_admin`의 새 credential provider는 추가하지 않는다.

## 2. 확정된 제품 결정

### 2.1 모델과 제작 방식

| 사용자 표시 이름 | API 모델 | 출력 |
|---|---|---|
| Nano Banana 2 | `gemini-3.1-flash-image` | 1:1, 1K, 1024×1024 |

Nano Banana 2를 선택하면 제작 방식은 `Clipper 템플릿 방식`으로 자동 고정한다.
제작 방식 선택 UI에는 `Clipper 템플릿 방식` 한 항목만 읽기 전용으로 표시하고,
`AI 통합 제작 방식`은 선택지에서 제외한다. 다음 이유를 짧게 설명한다.

> Nano Banana 2는 컷 이미지만 생성합니다. 음성, 자막, 타이틀과 최종 합성은
> Clipper 템플릿이 담당합니다.

이 모델로 만든 스토리보드의 `mode`는 항상 `clipper-template`이다. API 요청이
다른 mode를 보내더라도 Desktop Nest와 Web API 양쪽에서 거부한다.

### 2.2 해상도와 가격

임의의 가로·세로 px를 입력받지 않는다. Google Gemini API에는 다음 값을 고정해
전달한다.

```json
{
  "model": "gemini-3.1-flash-image",
  "input": "image shot prompt",
  "response_format": {
    "type": "image",
    "aspect_ratio": "1:1",
    "image_size": "1K"
  },
  "store": false
}
```

1:1·1K 결과는 1024×1024이고 표준 동기 호출의 이미지 출력 가격은 장당
USD 0.067이다. 프롬프트 입력과 thinking 출력 토큰 비용은 별도이며,
공급자가 반환한 usage metadata가 있으면 실제 사용량 기반 추정 비용에 포함한다.
Google이 실제 청구 금액을 응답하지 않으므로 화면에서는 이를 `실제 사용량 기반
추정 비용`으로 표현한다.

30초 영상의 목표 이미지 수는 약 10~12장이므로 이미지 출력 기본 비용은
USD 0.67~0.804이다. 스토리보드가 확정되면 범위가 아니라 실제 이미지 컷 수에
USD 0.067을 곱한 예상 비용을 표시한다.

### 2.3 최종 템플릿

Nano Banana 2 프로젝트에는 Full 템플릿을 사용하지 않는다. 템플릿 빌더가 기본
제공하는 다음 1:1 템플릿을 사용한다.

- family: `system.template-builder.default-shortform`
- ratio: `1:1`
- output canvas: 1080×1920
- content area: x=0, y=456, width=1080, height=1080

1024×1024 이미지는 기존 Clipper media fit 규칙으로 1080×1080 콘텐츠 영역을
채운다. 약 5.5% 확대되며 비율이 같으므로 자르지 않는다. 기존 AI 영상 모델은
계속 Full 템플릿을 사용한다.

## 3. 장면과 이미지 컷

### 3.1 두 계층의 역할

`scene`과 `image shot`을 구분한다.

- `scene`: 훅, 맥락, 근거, 결론처럼 이야기의 의미 단위
- `image shot`: 한 scene 안에서 실제 화면이 바뀌는 시각 단위

예를 들어 30초·5개 scene이라도 각 scene에 2~3개 image shot을 둘 수 있으며,
최종 영상에는 약 10~12장의 서로 다른 이미지가 사용된다. scene 수를 늘려
이야기 구조를 잘게 부수지 않는다.

### 3.2 이미지 전환 간격

- 목표 표시 시간: 이미지당 평균 2.5~3초
- 30초 목표 영상: 약 10~12개 image shot
- 각 scene에는 최소 1개 image shot이 있어야 한다.
- 이미지 수는 영상 전체 길이에 비례해 조정한다.
- 인접 image shot은 같은 프롬프트를 복제하지 않고 서로 다른 구도·피사체·행동을
  요구한다.

LLM은 내레이션의 의미 전환점과 시각적 변화가 필요한 지점을 기준으로 image shot을
계획한다. 목표 길이가 `D`초이고 scene 수가 `S`개일 때 validator가 허용하는 전체
image shot 수는 다음 범위다.

```text
minimum = max(S, ceil(D / 3.0))
maximum = max(minimum, ceil(D / 2.5))
```

따라서 30초 영상은 scene이 10개보다 많지 않은 일반적인 경우 10~12개 image shot을
허용한다. 결정론적 validator는 이 범위와 shot 순서, scene 소속, 비어 있지 않은
프롬프트를 검사한다.

Clipper 템플릿 방식에서는 TTS의 실제 길이가 최종 타임라인의 정본이다. TTS 생성 후
image shot 경계는 문장 또는 자막 구간 경계에 맞춰 실제 길이에 재배분한다. 이미지를
자동으로 추가 생성해 사용자가 승인한 호출 수를 늘리지는 않는다. 실제 TTS 때문에
평균 이미지 표시 시간이 크게 달라진 경우에는 확정된 shot 수와 비용을 생성 승인
화면에서 먼저 보여준다.

### 3.3 이미지 프롬프트 정책

각 image shot은 해당 narration 구간을 구체적으로 시각화한다.

- 장면에 맞는 인물, 사물, 장소, 행동, 조명, 구도를 구체적으로 요청한다.
- 인접 이미지가 같은 파동, 입자, 실루엣 같은 추상 표현을 반복하지 않게 한다.
- 세로 최종 영상 안의 정사각형 콘텐츠 영역에서 중요한 피사체가 잘 보이도록 한다.
- 메인 타이틀, 대사 자막, narration 문구를 이미지 픽셀에 생성하지 않는다.
- 읽을 수 있는 글자, 숫자, 로고, UI 문구, 워터마크를 새로 만들도록 요청하지 않는다.
- 오디오, 카메라 이동, 영상 전환을 이미지 공급자에게 요청하지 않는다.

타이틀과 대사 자막은 Clipper의 정확한 텍스트 레이어가 담당한다. 이 정책은
Nano Banana 2 이미지 경로에만 적용하고, 기존 영상 모델의 장면 고유 텍스트 정책은
바꾸지 않는다.

## 4. 데이터 계약

기존 `AiVideoProductionConfigV1`에 이미지 모델을 영상인 것처럼 넣지 않는다.
스토리보드가 사용하는 생성 미디어 설정을 구분할 수 있는 상위 계약을 둔다.

```text
productionConfig
  kind: generated-video | generated-image

generated-image
  schemaVersion
  model: nano-banana-2
  mode: clipper-template
  capabilitySnapshot
    provider: google_ai
    providerModelId: gemini-3.1-flash-image
    aspectRatio: 1:1
    imageSize: 1K
    width: 1024
    height: 1024
    estimatedUsdPerImage: 0.067
```

기존 저장 프로젝트의 video config는 읽기 호환성을 유지한다. Nano Banana 2
스토리보드에는 각 scene 아래에 다음 image shot 정보를 저장한다.

```text
imageShot
  id
  sceneId
  order
  narrationRange
  prompt
  plannedStartMs
  plannedEndMs
  motionPreset
  generatedAssetRef?
```

`motionPreset`은 `zoom-in`, `pan-left`, `pan-right`를 image shot 전역 순서대로
반복한다. 같은 scene이 끝나도 순환 순서는 이어진다.

## 5. AI 이미지 작업

### 5.1 Web API

영상 job과 별도의 persisted AI image job 모듈을 둔다.

```text
POST /.../image-generation/jobs
GET  /.../image-generation/jobs/:jobId
GET  /.../image-generation/jobs/:jobId/result
POST /.../image-generation/jobs/:jobId/result-ack
```

책임은 다음과 같다.

- idempotency key와 입력 digest 검사
- Google AI credential의 서버 측 해석
- Gemini Interactions API `POST /v1beta/interactions` 호출
- 이미지 전용 `response_format`과 1:1·1K 강제
- 응답 `model_output`의 inline image bytes와 MIME type 검증
- provider usage와 오류 정보 저장
- 인증된 result endpoint로 Desktop Nest에 이미지 전달

이미지 생성 응답은 긴 영상 생성 operation과 달리 한 요청에서 완료될 수 있다.
그렇더라도 job을 먼저 영속화해 서버 재시작 뒤 성공·실패 상태와 사용량을 잃지 않게
한다. 동일 승인과 idempotency key로 공급자 호출을 중복 제출하지 않는다.

Google은 이 이미지 결과에 다시 내려받을 수 있는 provider URL을 보장하지 않으므로
Web API는 성공 응답의 원본 image bytes를 job result blob으로 임시 보관한다.
Desktop Nest가 result를 내려받아 checksum 검증과 로컬 저장을 완료했다는 ack를
보내면 blob을 삭제한다. ack 전 재시작이나 일시적인 네트워크 실패에서는 같은
result를 다시 내려받을 수 있다. blob 삭제 뒤에도 job metadata, checksum, usage와
비용 정보는 DB에 유지한다. 영구 원본 파일의 단일 출처는 Desktop Nest의
`CLIPPER_DATA_DIR`이다. ack를 받지 못한 blob은 성공 시각부터 7일간 보관한 뒤
삭제하고 job을 `output_expired`로 표시한다.

### 5.2 Desktop Nest

Desktop Nest는 image shot마다 다음 흐름을 제공한다.

1. preflight에서 모델, 1:1·1K, 이미지 한 장, 예상 USD 비용을 반환한다.
2. 사용자 승인 ID와 함께 Web API image job을 제출한다.
3. 결과가 준비되면 인증된 endpoint에서 이미지를 내려받는다.
4. 파일 signature, MIME type, 크기, 1:1 비율과 실제 px를 검사한다.
5. `CLIPPER_DATA_DIR` 아래 프로젝트·storyboard revision 전용 경로에 영구 저장한다.
6. checksum, 파일 크기, px, provider request ID, credential revision, usage와 비용을
   로컬 job 상태에 저장한다.

기존 AI 영상 파일과 이미지 파일은 저장 경로와 job type을 분리한다. 성공한 파일은
새 시도 때문에 덮어쓰지 않는다.

### 5.3 오류와 재시도

- 공급자 HTTP 상태, Google 오류 code·message와 실패 시각을 저장한다.
- 빈 응답, PNG·JPEG·WebP가 아닌 MIME, 손상 이미지, 1024×1024가 아닌 결과는
  해당 image shot의 검증 실패로 기록한다.
- 실패한 image shot만 새 비용 승인 후 재시도할 수 있다.
- 자동 provider 재제출은 하지 않는다.
- 성공한 image shot은 다른 shot 실패 때문에 다시 생성하지 않는다.
- 앱과 서버를 재시작해도 성공·실패·승인·provider 정보를 복구한다.

## 6. 사용자 경험

### 6.1 스토리보드 생성

스토리보드 새로 만들기에서 `Nano Banana 2`를 선택할 수 있다. 선택 즉시 제작 방식
영역은 `Clipper 템플릿 방식`으로 고정되고 1:1·1K 설명을 표시한다.

스토리보드 결과에는 다음을 보여준다.

- scene별 narration
- scene 안의 image shot 목록
- 각 image shot의 시각 설명과 예상 표시 시간
- 전체 이미지 수
- 예상 이미지 생성비

### 6.2 제작 단계

기존 `2. AI 영상 생성`은 프로젝트의 media kind에 따라 제목과 내용을 바꾼다.

- 영상 모델: `2. AI 영상 생성`
- Nano Banana 2: `2. AI 이미지 생성`

이미지 경로에서는 각 행에 thumbnail, prompt 요약, 실제 표시 시간, 움직임 효과,
예상 비용, 상태, 오류, 생성·재시도 동작을 표시한다. 모든 이미지를 한꺼번에 생성하는
동작을 추가하더라도 총 이미지 수와 총 예상 비용을 한 번 더 승인받고, 내부적으로는
shot별 idempotency를 유지한다.

### 6.3 최종 렌더

Clipper 최종 렌더 adapter는 image shot을 기존 clip `mediaSlots`로 변환한다.

- 각 slot의 시작·종료 시각은 TTS 타임라인과 일치한다.
- slot의 이미지 asset ID를 연결한다.
- `zoom-in → pan-left → pan-right` motion preset을 순환 적용한다.
- 기존 default 1:1 template preset을 사용한다.
- 기존 Clipper main title, spoken-word subtitle, TTS, BGM, 효과음 합성을 사용한다.
- 일반 Clipper와 같은 실행 큐, progress event, 결과 artifact, 프로젝트 보관함을
  사용한다.

최종 렌더는 모든 image shot과 TTS가 준비된 뒤에만 활성화한다. 재렌더는 기존 생성
이미지를 재사용하며 Google 이미지 생성 비용을 추가하지 않는다.

## 7. 호환성과 범위

이번 변경은 다음을 바꾸지 않는다.

- 기존 Gemini Omni, Seedance 2.0, Veo 스토리보드와 AI 영상 job
- 기존 영상 모델의 Full 템플릿 선택
- 기존 스토리보드 history와 최종 렌더 history 보존 정책
- 프로젝트 보관함의 AI 숏폼 디렉터 분류
- 운영 프로필의 목표 길이와 TTS 기준 최종 길이 정책

이번 범위에는 다음을 포함하지 않는다.

- 512, 2K, 4K 해상도 선택 UI
- Nano Banana 2 Lite나 Nano Banana Pro
- 사용자가 임의 px나 aspect ratio를 입력하는 기능
- 이미지 편집·부분 수정·reference image 입력
- Google Search grounding
- 새로운 crossfade 전환 효과
- AI가 이미지 안에 정확한 데이터 그래프나 자막을 생성하는 방식

## 8. 검증

### 8.1 단위·계약 테스트

- 모델 catalog가 Nano Banana 2를 1:1·1K·USD 0.067로 노출한다.
- Nano Banana 2는 `clipper-template`만 허용한다.
- 스토리보드 prompt가 `generated-image`와 여러 image shot을 요구한다.
- 30초 계획이 약 10~12개 image shot을 만들고 각 scene이 최소 한 장을 갖는다.
- validator가 누락·중복 순서, 빈 prompt와 잘못된 scene 참조를 거부한다.
- motion preset이 `zoom-in`, `pan-left`, `pan-right` 순서로 반복된다.
- Web API가 정확한 Gemini model과 1:1·1K request를 보낸다.
- idempotency replay가 공급자 호출을 중복 제출하지 않는다.
- provider 오류와 usage가 재시작 뒤에도 유지된다.
- Desktop이 파일 signature, MIME, px와 비율을 검사한다.
- final render adapter가 기본 1:1 template과 image media slots를 사용한다.
- 기존 영상 모델이 계속 Full template과 AI video job을 사용한다.

### 8.2 통합 검증

- 30초 후보로 새 Nano Banana 2 스토리보드를 만든다.
- scene 수와 별개로 약 10~12개 image shot이 생성되는지 확인한다.
- 비용 승인 전 Google 호출이 없는지 확인한다.
- 일부 image shot 실패 뒤 성공한 이미지를 유지한 채 해당 shot만 재시도한다.
- 앱과 Web API 재시작 뒤 상태와 로컬 파일이 복구되는지 확인한다.
- TTS를 생성하고 이미지 전환이 자막 의미 경계와 대체로 일치하는지 확인한다.
- 최종 렌더에서 기본 1:1 템플릿, 타이틀, 자막, TTS, BGM·효과음과 이미지 motion이
  기존 Clipper 파이프라인으로 합성되는지 확인한다.
- 결과가 AI 숏폼 디렉터와 프로젝트 보관함에 모두 나타나는지 확인한다.

실제 Google 호출은 자동 테스트의 필수 조건으로 두지 않는다. provider adapter는
고정된 fixture 응답으로 검증하고, 실제 비용이 발생하는 호출은 사용자가 등록한
credential로 명시적으로 승인한 smoke test에서만 수행한다.

## 9. 공식 참조

- Gemini Interactions API 개요:
  `https://ai.google.dev/gemini-api/docs/interactions-overview`
- Nano Banana 이미지 생성과 1:1·1K REST 형식:
  `https://ai.google.dev/gemini-api/docs/image-generation`
- Gemini Developer API 가격:
  `https://ai.google.dev/gemini-api/docs/pricing`

2026-08-07 기준 신규 통합에는 Interactions API가 권장되므로 `store:false`인
stateless 단일 이미지 요청을 사용한다.
