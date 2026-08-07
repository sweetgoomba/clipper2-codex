# Shortform Director Veo 모델과 스토리보드 이력 설계

Date: 2026-08-05
Status: 사용자 문서 검토 승인 완료; 구현 계획 작성 완료

## 1. 목표

Shortform Director의 영상 후보 한 개에서 스토리보드를 여러 번 생성하고, 과거 결과를
덮어쓰지 않은 채 다시 열어볼 수 있게 한다.

동시에 Google 영상 모델 두 개를 추가한다.

- `Veo 3.1 Lite Generate`
- `Veo 3.1 Fast Generate`

스토리보드 화면은 실행 기록 관리 화면처럼 시작하지 않는다. 페이지 진입 시 현재 선택된
후보의 최신 스토리보드 전체를 바로 보여주고, 사용자가 원할 때만 이전 스토리보드 목록을
연다.

대상 저장소는 다음과 같다.

- `desktop/clipper_angular`
- `desktop/clipper_nestjs`
- `web/clipper_web_api`
- 크로스 저장소 설계 문서는 `clipper_docs`

Web Admin은 기존 Google AI 자격 증명을 재사용하므로 이번 변경 대상이 아니다.

## 2. 현재 상태와 문제 원인

스토리보드 생성 결과는 이미 매번 별도로 저장된다.

- 생성 요청마다 새로운 `video-plan` run이 생긴다.
- run마다 새로운 `ShortformDirectorProject`가 생긴다.
- 프로젝트에는 그때 선택한 영상 모델과 제작 방식 snapshot이 저장된다.

따라서 데이터가 실제로 덮어써지는 구조는 아니다. 현재 Angular store가 동일 후보와
일치하는 성공 run 중 최신 한 개만 찾아 `project` signal에 넣고, 나머지를 버리기 때문에
사용자에게 덮어쓴 것처럼 보인다.

현재 구조를 project 내부 revision 배열로 바꾸지 않는다. 스토리보드별 내레이션, AI 영상
job, 로컬 파일과 렌더 상태도 project에 연결되므로, 기존의 run/project 한 쌍을
스토리보드 이력 단위로 유지하는 편이 격리와 복구에 유리하다.

## 3. 확정된 사용자 경험

### 3.1 기본 화면

동일 후보의 스토리보드가 하나 이상이면 다음 순서로 표시한다.

1. 후보 제목과 현재 스토리보드 요약
2. `스토리보드 #N · 최신` 상태
3. 선택 모델, 제작 방식, 목표 또는 실제 길이
4. `다른 스토리보드 N개` 버튼
5. `새 스토리보드 만들기` 버튼
6. 현재 스토리보드의 전체 장면
7. 현재 스토리보드에 속한 내레이션·AI 영상·최종 렌더 영역

`다른 스토리보드 N개`는 현재 선택 항목을 제외한, 열어볼 수 있는 스토리보드 수다.
이전 기록 목록은 기본 화면에 고정하지 않고 버튼을 눌렀을 때 Material menu 또는
popover로 연다. 영구 좌측 sidebar와 목록 전용 첫 화면은 사용하지 않는다.

스토리보드가 아직 없으면 모델·제작 방식과 비용 승인을 받는 생성 화면을 바로 표시한다.

### 3.2 장면 배치

장면은 2열 grid가 아니라 하나의 세로 흐름으로 배치한다.

```text
장면 1
  의도와 설명
  내레이션
  컷 1
  컷 2

장면 2
  의도와 설명
  내레이션
  컷 1
```

논리 장면 하나에는 여러 `shot`이 들어갈 수 있다. UI에서는 이를 장면 아래에 순서대로
중첩해 보여준다. 모델 최대 길이 때문에 한 장면이 여러 shot으로 나뉘어도 별개의 장면처럼
보이게 만들지 않는다.

### 3.3 이전 스토리보드 전환

이력 항목은 다음 정보를 짧게 보여준다.

- 순번과 최신 여부
- 생성 시각
- 영상 모델
- 제작 방식
- 길이
- 상태

성공한 항목을 선택하면 해당 run의 project 전체를 불러오고, 장면과 그 project에 속한
후속 제작 상태를 모두 전환한다. 과거 항목을 열어도 데이터는 수정되지 않는다.

진행 중인 항목은 상태만 보여주고 완료 후 열 수 있다. 실패한 항목은 실패 상태를
보여주되 project가 생성된 경우에만 진단 정보를 열 수 있다. `다른 스토리보드 N개`의
기본 개수는 성공해서 열 수 있는 항목만 센다.

### 3.4 새 스토리보드 생성

`새 스토리보드 만들기`를 누르면 현재 스토리보드를 지우지 않고 생성 설정 영역을 연다.
여기서는 매번 다음 값을 자유롭게 다시 고른다.

- 영상 모델
- `Clipper 템플릿 방식` 또는 `AI 통합 제작 방식`

선택값이 바뀔 때마다 새 preflight를 조회하고, 표시된 모델·자격 증명·예상 비용을 다시
승인한다. 생성 성공 시 새 run/project가 최신 항목이 되고 즉시 전체 화면에 선택된다.
취소하거나 실패하면 원래 보던 스토리보드는 그대로 유지된다.

기존 프로젝트의 모델이나 제작 방식은 변경하지 않는다. 설정 변경은 항상 새
스토리보드를 만든다는 뜻이다.

## 4. 스토리보드 이력 API

### 4.1 선택한 접근

Desktop Nest에 후보 단위 요약 endpoint를 추가한다.

```http
GET /v1/projects/shortform-director/candidate-production/
    candidate-runs/:candidateRunId/candidates/:candidateId/storyboards
```

실제 URL은 한 줄이며 응답은 raw 객체다.

```json
{
  "schemaVersion": "shortform-director-storyboard-history.v1",
  "candidateRunId": "run.director.example",
  "candidateId": "candidate.director.example",
  "items": [
    {
      "runId": "run.local.example",
      "projectId": "shortform_director_project_example",
      "status": "succeeded",
      "startedAt": "2026-08-05T12:00:00.000Z",
      "finishedAt": "2026-08-05T12:00:08.000Z",
      "title": "스토리보드 제목",
      "model": "veo-3.1-fast",
      "mode": "clipper-template",
      "durationMs": 30000,
      "sceneCount": 5,
      "shotCount": 6,
      "canOpen": true
    }
  ]
}
```

`items`는 `startedAt` 내림차순이다. 이 endpoint는 기존 run, 결과 artifact와 project를
서버 내부에서 결합할 뿐 새로운 영속화 컬렉션을 만들지 않는다.

기존 성공 run은 `candidate-production-result` artifact의 `candidateRunId`와
`candidateId`로 일치 여부를 판단한다. 실행 중 또는 실패 run은 저장된
`candidate-production-input` artifact로 가능한 범위에서 일치 여부를 판단한다. 후보
lineage를 저장하기도 전에 실패한 불완전 run은 특정 후보의 이력으로 단정하지 않고
제외한다.

### 4.2 기존 endpoint 유지

다음 endpoint는 그대로 유지한다.

- 후보별 preflight
- 새 candidate production run 생성
- profile별 run 목록
- run 단건
- run 결과
- run project

이력 요약을 선택한 뒤 전체 project를 여는 동작은 기존
`GET .../runs/:runId/project`를 사용한다. 따라서 큰 project 배열을 이력 응답에 반복해서
넣지 않는다.

### 4.3 권한과 하위 호환

- 모든 조회는 기존 `ownerSubjectId` 경계를 유지한다.
- 요청 후보가 현재 사용자에게 속하는지 기존 candidate 조회 경로로 확인한다.
- 기존 로컬 run/project/artifact 파일은 마이그레이션하지 않는다.
- 모델 snapshot이 없는 오래된 project는 기존 기본값을 적용하되 이력 조회를 실패시키지
  않는다.
- 응답 봉투를 추가하지 않고 Nest raw 응답 규칙을 유지한다.

## 5. Angular 상태와 화면 구조

현재 하나뿐인 `project` 상태를 다음 개념으로 분리한다.

```text
storyboardHistory
selectedStoryboardRunId
selectedProject
isCreatingStoryboard
draftProductionConfig
preflight
```

페이지 진입 흐름은 다음과 같다.

1. 후보별 이력을 한 번 조회한다.
2. 성공한 최신 항목을 기본 선택한다.
3. 선택한 run의 project를 조회한다.
4. 성공 항목이 없으면 새 스토리보드 생성 상태로 들어간다.

이력 menu를 여는 것은 상태 조회나 project 전환을 발생시키지 않는다. 사용자가 항목을
선택할 때만 project를 가져온다.

`draftProductionConfig`는 선택된 과거 project의 snapshot과 별도다. 새 생성 중 모델이나
제작 방식을 바꿔도 현재 project의 표시는 바뀌지 않는다.

기존 setup card, 비용 승인 계약과 project 제작 컴포넌트를 재사용한다. 페이지의 기본
순서만 `설정 → 실행 기록 → 결과`에서 `현재 결과 → 필요할 때 이력/새 생성`으로 바꾼다.

## 6. 추가 영상 모델

### 6.1 모델 catalog

| 사용자 표시 이름 | 내부 선택 ID | Google API 모델 |
|---|---|---|
| Veo 3.1 Lite Generate | `veo-3.1-lite` | `veo-3.1-lite-generate-preview` |
| Veo 3.1 Fast Generate | `veo-3.1-fast` | `veo-3.1-fast-generate-preview` |

두 모델은 다음 capability를 갖는다.

- 720×1280
- 9:16
- 직접 생성 길이 4초, 6초 또는 8초
- 스토리보드 shot 최대 길이 8초
- 네이티브 오디오
- 이번 범위에서 video extension은 사용하지 않음

가격 snapshot은 720p 생성 기준으로 둔다.

- Lite: USD 0.05/초
- Fast: USD 0.10/초

가격은 공급자 정책 변경 시 catalog와 승인 계약을 함께 갱신해야 한다.

### 6.2 계획 길이와 공급자 요청 길이

스토리보드와 TTS 정렬 결과에는 필요한 실제 `plannedDurationSeconds`를 유지한다.
Google 요청 직전에 다음 지원 길이로 올림한다.

```text
0초 초과 ~ 4초  → 4초
4초 초과 ~ 6초 → 6초
6초 초과 ~ 8초 → 8초
```

예를 들어 계획 길이가 7.019초면 공급자에는 8초를 요청한다. 최종 Clipper 렌더는 해당
shot을 7.019초만 사용하고 남은 끝부분을 자른다. 생성 파일이 계획 길이보다 짧으면
기존 규칙처럼 검증 실패로 처리한다.

예상 비용과 사용자가 승인하는 비용은 계획 길이가 아니라 실제 provider 요청 길이로
계산한다. 7.019초 shot의 예상 비용은 다음과 같다.

- Lite: `8 × 0.05 = USD 0.40`
- Fast: `8 × 0.10 = USD 0.80`

스토리보드 LLM에는 `maxShotSeconds = 8`을 전달한다. 논리 장면이 8초를 넘으면 기존
compiler가 여러 shot으로 나눈다. 하나의 장면에 영상 하나만 강제하지 않는다.

### 6.3 Google Veo transport

Web API에 Google Veo 전용 transport를 추가한다.

제출:

```http
POST https://generativelanguage.googleapis.com/v1beta/
     models/{model}:predictLongRunning
```

요청 핵심 값:

```json
{
  "instances": [{ "prompt": "..." }],
  "parameters": {
    "numberOfVideos": 1,
    "resolution": "720p",
    "aspectRatio": "9:16",
    "durationSeconds": 8
  }
}
```

반환된 long-running operation `name`을 job에 저장하고 완료될 때까지 조회한다. 외부에
보이는 `providerRequestId`에는 operation name 원문 대신 `veo-` 접두사가 붙은 SHA-256
식별자를 사용한다. 완료
응답의 `generatedSamples[0].video.uri`를 Google API key가 포함된 서버 간 요청으로
읽어 Desktop Nest에 인증된 스트림으로 전달한다.

Veo operation name은 현재 Web API job 테이블의 `provider_file_id` 컬럼에 provider
resource identifier로 저장한다. DB migration 없이 재시작 후 polling을 복구하기 위한
최소 변경이다. 도메인 transport 타입에서는 이를 `operationName`으로 표현하고 Google
Omni의 `fileId`와 섞지 않는다.

public job 응답과 로그에는 API key와 다운로드 URI를 노출하지 않는다.

### 6.4 제작 방식별 오디오

`Clipper 템플릿 방식`에서는 Veo가 환경음과 효과음만 생성하도록 요청한다.

- 나레이션 금지
- 인물 대사 금지
- 대사를 따라가는 자막 금지
- BGM 금지
- 장면 자체에 필요한 글자·숫자·그래픽은 허용
- ambient sound와 scene-appropriate SFX 허용

`AI 통합 제작 방식`에서는 기존 계약대로 영상, 나레이션 또는 대화, 화면 텍스트, 효과음,
BGM을 함께 요청한다. 모델이 만든 음성과 텍스트 정확성을 Clipper가 보장하거나 개별
트랙으로 분리할 수 있다고 가정하지 않는다.

## 7. 오류와 복구

- Google HTTP 오류의 안전한 status, code, message와 응답 요약을 기존 provider failure
  snapshot에 저장한다.
- 같은 컷을 다시 생성하는 동작은 새 비용 승인을 거쳐 새 provider job을 만든다.
- Web API가 재시작되어도 저장한 operation name으로 상태 조회를 계속할 수 있다.
- operation이 성공했지만 결과 URI가 없거나 다운로드 파일이 유효한 MP4가 아니면
  공급자 또는 파일 검증 실패로 구분한다.
- 이력 전환 실패는 현재 보던 project를 지우지 않고 해당 항목에 오류를 표시한다.
- 새 스토리보드 생성 실패도 현재 선택된 스토리보드를 유지한다.

## 8. 범위 제외

이번 변경에는 다음을 포함하지 않는다.

- Veo video extension
- 하나의 provider 결과를 이어 붙여 8초보다 긴 단일 생성 요청처럼 취급하는 기능
- S3 또는 외부 object storage
- 기존 스토리보드 project의 모델·제작 방식 변경
- AI 생성 화면 텍스트의 OCR 정확성 보정
- 기존 저장 파일의 일괄 migration
- 패키지 앱 빌드와 유료 provider 실제 호출

## 9. 검증 기준

### 9.1 Web API

- 두 Veo 모델이 selectable catalog에 노출된다.
- model ID에 맞는 `predictLongRunning` URL을 사용한다.
- 720p, 9:16, 4·6·8초 요청 body를 검증한다.
- 7.019초 계획이 8초 요청과 8초 비용으로 변환된다.
- mock fetch로 submit, poll, download를 검증한다.
- operation name 저장 후 service 재생성 상황에서도 polling할 수 있다.
- Omni와 Seedance 기존 경로가 회귀하지 않는다.

### 9.2 Desktop Nest

- capability parser와 저장 project가 네 모델을 모두 수용한다.
- Veo shot 최대 길이가 8초로 계획 입력과 compiler에 전달된다.
- 한 장면이 여러 shot으로 나뉠 수 있다.
- provider 요청 길이와 예상 비용이 같은 4·6·8초 기준을 사용한다.
- 후보별 이력이 최신순으로 반환되고 다른 후보의 run은 제외된다.
- 기존 run/project JSON도 계속 읽힌다.

### 9.3 Desktop Angular

- 페이지 진입 시 최신 성공 스토리보드 전체가 먼저 보인다.
- 장면은 단일 세로 목록이며 shot은 소속 장면 안에 표시된다.
- 이전 목록은 `다른 스토리보드 N개`를 열기 전에는 보이지 않는다.
- 이력 선택 시 해당 project와 후속 제작 상태가 전환된다.
- 새 생성에서는 모델·제작 방식을 다시 선택할 수 있다.
- 생성 취소·실패 시 현재 project가 유지된다.
- Lite와 Fast가 서로 다른 이름과 비용으로 선택된다.
- 기존 Gemini Omni와 Seedance 선택도 유지된다.

## 10. 구현 원칙

- 각 변경은 실패하는 테스트를 먼저 추가한 뒤 최소 구현으로 통과시킨다.
- 공급자 테스트는 HTTP mock만 사용하고 실제 유료 호출을 하지 않는다.
- 기존 dirty worktree와 관련 없는 변경을 보존한다.
- 사용자가 직접 실행하는
  `npm run build:app:mac:arm64:local-api` 패키지 빌드는 수행하지 않는다.
- 사용자 요청 전에는 commit이나 push를 하지 않는다.

## 11. 참고

- Google Gemini API video generation:
  <https://ai.google.dev/gemini-api/docs/video>
- Google Gemini API pricing:
  <https://ai.google.dev/gemini-api/docs/pricing>
- 기존 AI 영상 제작 설계:
  `architecture/2026-08-05-shortform-director-ai-video-production-design.md`
- 기존 AI 생성 화면 콘텐츠 설계:
  `architecture/2026-08-05-shortform-director-ai-generated-visual-content-design.md`
