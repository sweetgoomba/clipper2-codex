# Shortform Director AI 영상 제작 설계

Date: 2026-08-05
Status: 사용자 대화 설계 승인 완료; 문서 검토 대기

## 1. 목표

현재 `feat/shortform-director-storyboard-only`의 결과 중심 조사·주제·영상 후보 흐름은
유지하면서, 선택한 영상 후보에서 다음 경로를 다시 제공한다.

```text
운영 프로필
  → 조사 주제
  → 영상 후보
  → 영상 모델·제작 방식 선택
  → 스토리보드 비용 승인·생성
  → 스토리보드 검토
  → 장면별 AI 영상 비용 승인·생성
  → Clipper 최종 렌더
  → 완성 영상 미리보기·로컬 저장
```

이 기능은 이전 제작 파이프라인을 통째로 되돌리지 않는다. 현재 브랜치의
스토리보드 lineage와 기존 Clipper 렌더러를 연결하고, 이번 범위에 필요한 생성 영상
작업·로컬 저장·최종 합성만 복원한다.

대상 저장소는 다음과 같다.

- `desktop/clipper_angular`
- `desktop/clipper_nestjs`
- `web/clipper_web_api`
- `web/clipper_web_admin`
- 크로스 저장소 설계 문서는 `clipper_docs`

`desktop/clipper_python`과 `desktop/clipper_electron`은 기존 빌드·패키징 경로가 새
정적 에셋을 자동 포함하지 못하는 경우가 아니라면 변경하지 않는다.

## 2. 확정된 제품 결정

### 2.1 운영 프로필의 목표 길이

모든 운영 프로필에 `targetDurationSeconds`를 둔다.

- 기본값: `30`
- 입력 범위: `15` 이상 `60` 이하
- 정수만 허용하므로 `23`, `37` 같은 값도 유효하다.
- 기존 프로필에는 읽기 마이그레이션 시 기본값 `30`을 적용한다.

목표 길이는 LLM이 대사량과 스토리보드 규모를 정하는 기준이다. 최종 영상 길이를
강제로 자르는 상한이 아니다.

`Clipper 템플릿 방식`의 실제 최종 길이는 생성된 TTS 타임라인에 맞춘다. 예를 들어
목표가 30초이고 TTS가 34.7초이면 최종 영상도 34.7초다. TTS를 빠르게 재생하거나
자르지 않는다.

### 2.2 사용자에게 보이는 영상 모델

| 표시 이름 | 실제 API 모델 | 생성 규칙 |
|---|---|---|
| Gemini Omni | `gemini-omni-flash-preview` | 720p, 9:16, shot당 3~10초 |
| Seedance 2.0 | `bytedance/seedance-2.0/text-to-video` | 720p, 9:16, shot당 4~15초 |

두 모델의 생성 소스는 720×1280이고 최종 Clipper 렌더는 1080×1920이다. 종횡비가
같으므로 생성 영상을 1.5배 확대하며 자르지 않는다. 템플릿 글자와 gradient는
1080×1920 캔버스에서 직접 렌더해 선명도를 유지한다.

### 2.3 제작 방식

사용자는 모델과 별도로 다음 제작 방식 하나를 고른다.

#### Clipper 템플릿 방식

- AI 모델은 실제 생성 영상과 환경음·효과음만 만든다.
- AI 영상은 장면에 필요한 정확한 화면 문구·숫자·차트·표지판을 함께 생성할 수 있다.
- AI 영상 프롬프트는 나레이션, 캐릭터 대사, 대사를 따라가는 자막, BGM을 금지한다.
- Clipper가 TTS, 정확한 자막, 기본 `full` 템플릿과 사용자가 선택한 BGM을 합성한다.
- AI 영상에 포함된 환경음과 효과음은 유지한다.
- 기존 Shortform Director의 Clipper narration preset 선택을 재사용한다.
- 기존 일반 숏폼의 BGM catalog와 선택 UI를 재사용하며 `선택 안 함`도 허용한다.
- 기본 선택값이다.

#### AI 통합 제작 방식

- AI 모델이 영상, 나레이션 또는 인물 대화, 자막, 효과음과 BGM을 함께 만든다.
- Clipper 템플릿, Clipper TTS, 별도 Clipper 자막은 사용하지 않는다.
- Clipper는 shot 연결, 음량 정규화, 최종 인코딩만 담당한다.

AI 통합 방식은 장면과 음성의 자연스러운 결합이나 립싱크가 장점이지만, 여러 shot에서
목소리·자막 글꼴·자막 정확도가 달라질 수 있고 생성 후 개별 수정도 어렵다. 이 차이를
선택 화면에 짧게 설명한다.

### 2.4 선택 시점

영상 모델과 제작 방식은 스토리보드를 만들기 전에 고른다. 모델별 shot 길이와 제작
방식별 대사·자막·오디오 프롬프트가 다르기 때문이다.

스토리보드가 생성된 뒤 모델 또는 제작 방식을 바꾸면 기존 스토리보드를 변환하지 않고
새 스토리보드 생성과 그 비용 승인을 다시 진행한다.

## 3. 시스템 책임

### 3.1 Desktop Angular

- 프로필 생성·수정 화면의 목표 길이 숫자 입력
- 영상 후보에서 스토리보드 설정 화면 진입
- `Gemini Omni` / `Seedance 2.0` 모델 선택
- `Clipper 템플릿 방식` / `AI 통합 제작 방식` 선택
- 단계별 예상 비용 승인
- 스토리보드와 shot 검토
- Clipper 방식에서 기존 TTS preset·속도와 선택적 BGM 지정
- shot별 생성·다운로드·실패 상태 표시
- 실패한 shot의 개별 재생성과 추가 비용 승인
- 최종 렌더 진행, 완성 영상 미리보기, 로컬 위치 열기

기존 영상 후보 카드의 정보 그리드와 기술 정보 접기 구조는 유지한다. 이번 작업을 이유로
후보 카드를 축약하거나 실행 기록 중심 UI로 되돌리지 않는다.

### 3.2 Desktop Nest

- 프로필, 스토리보드, 모델·제작 방식 snapshot의 로컬 영속화
- 스토리보드 shot 길이의 결정론적 검증과 분할
- Clipper 방식의 TTS 생성·실제 길이 측정·shot 타임라인 확정
- Web API 생성 job 제출·상태 조회·결과 스트림 다운로드
- 생성 MP4의 로컬 저장, 검사, 재시작 복구
- 기존 Clipper 렌더 입력으로 변환
- 템플릿·TTS·자막·효과음·BGM 합성 또는 AI 통합 영상 연결
- 최종 1080×1920 렌더와 로컬 결과 저장

Desktop Nest가 이 기능의 로컬 작업 상태와 파일의 단일 출처다.

### 3.3 Web API

- Gemini와 FAL 자격 증명의 서버 측 해석
- 모델별 provider adapter
- 장시간 생성 작업의 제출, 상태 확인, 결과 조회
- 공급자 결과를 인증된 스트림으로 Desktop Nest에 전달
- 예상 비용 계약과 가능한 경우 실제 provider usage 반환

Web API는 생성 MP4를 영구 보관하지 않는다. 공급자 결과와 Desktop Nest 사이를
스트리밍하며 브라우저나 Electron renderer에 API key를 노출하지 않는다.

### 3.4 Web Admin

기존 API key 관리 화면에 `fal` provider를 추가한다.

- 암호화된 DB 저장
- active / standby / disabled 상태
- 연결 시험
- key 교체와 revision 관리
- 런타임 상태 표시

기존 Gemini 자격 증명은 Gemini Omni에도 재사용한다. FAL key는 Web Admin과 Web API
밖으로 평문 노출하지 않는다.

## 4. 스토리보드 계약

스토리보드 실행에는 사용자가 선택한 값과 그 시점의 모델 능력을 함께 저장한다.

```text
storyboardRun
  modelSelection
    displayName
    provider
    apiModelId
  productionMode
  capabilitySnapshot
    minShotSeconds
    maxShotSeconds
    resolution
    aspectRatio
    audioPolicy
  targetDurationSeconds
  clipperStyleSnapshot?
    narrationPresetId
    speakerId
    speed
    bgmId?
  scenes[]
    narrative intent
    narration/dialogue
    captions
    shots[]
      shotId
      visual prompt
      plannedDurationSeconds
      narration/caption references
```

`capabilitySnapshot`은 나중에 provider 설정이나 가격이 바뀌어도 기존 실행이 어떤
조건으로 만들어졌는지 설명하기 위한 기록이다. 유효성 검사는 프롬프트에만 맡기지
않고 Desktop Nest의 결정론적 validator가 다시 수행한다.

스토리보드의 논리 장면 하나가 모델 최대 길이보다 길 수는 있다. 대신 그 안의 실제 생성
단위인 `shots`는 반드시 해당 모델의 최소·최대 길이를 만족하도록 나눈다.

## 5. 생성 순서와 시간 기준

### 5.1 공통 스토리보드 생성

1. 영상 후보에서 `스토리보드 만들기`를 누른다.
2. 모델과 제작 방식을 선택한다.
3. 선택값, 목표 길이, 예상 LLM 비용을 확인하고 승인한다.
4. 선택한 능력 제한을 포함해 스토리보드를 생성한다.
5. validator가 shot 수, 순서, 길이, 대사·자막 정책을 검사한다.
6. 사용자가 결과를 검토한다.

### 5.2 Clipper 템플릿 방식

스토리보드 승인 뒤 순서는 다음과 같다.

1. 기존 Clipper narration preset과 속도를 선택하고, BGM은 선택하거나 끈다.
2. 스토리보드의 정확한 대사로 기존 Clipper TTS를 생성한다.
3. TTS의 실제 재생 길이와 문장·자막 타임스탬프를 측정한다.
4. 실제 TTS 길이를 최종 영상 타임라인으로 확정한다.
5. 논리 장면을 보존하면서 각 shot의 길이를 모델 제한에 맞게 다시 배분한다.
6. 확정된 shot별 예상 영상 생성 비용을 보여주고 한 번 승인받는다.
7. AI 영상과 환경음·효과음을 생성한다.
8. 모든 shot이 준비되면 Clipper 렌더러에서 합성한다.

선택한 narration preset의 ID뿐 아니라 실제 `speakerId`와 `speed` snapshot을 프로젝트에
남긴다. 나중에 preset이 수정돼도 과거 프로젝트 TTS의 재현 조건이 바뀌지 않게 한다.
Clipper 방식에서 유효한 narration preset이 없으면 TTS 생성 버튼을 비활성화하고 기존
TTS 관리 화면으로 안내한다. AI 통합 방식에서는 이 선택 UI를 숨긴다.

첫 provider 영상 job이 제출되면 그 production revision의 모델, 제작 방식,
`speakerId`, `speed`와 TTS 타임라인을 잠근다. 이후 목소리나 속도를 바꾸려면 새
production revision에서 TTS와 shot 계획을 다시 만들고, 필요한 AI 영상 비용을 다시
승인받는다. 기존 revision과 생성 파일은 보존하며 새 provider 호출을 자동으로 시작하지
않는다.

BGM은 TTS와 shot 길이에 영향을 주지 않는다. BGM을 바꾸거나 끄는 작업은 기존 AI
영상을 재사용해 최종 렌더만 다시 실행하며 provider 영상 생성 비용을 추가하지 않는다.

목표 길이와 실제 TTS 길이가 달라도 사용자에게 대사를 줄이라고 요구하지 않는다.
스토리보드의 목표 길이는 계획 기준이고 실제 TTS가 최종 시간의 정본이다.

TTS가 34.7초처럼 소수 길이일 때도 최종 영상은 34.7초다. Seedance처럼 정수 초 길이만
요청할 수 있는 provider에는 필요한 길이보다 짧지 않은 지원 길이를 요청하고, 생성
영상의 음성이 없는 끝부분을 shot 계획 길이에 맞게 자른다. shot 길이 배분은 마지막
shot이 모델 최소 길이보다 작아지지 않도록 전체 shot에 분산한다.

- 생성 영상이 계획보다 길면 영상 끝과 해당 효과음을 짧게 fade-out하며 자를 수 있다.
- 생성 영상이 계획보다 짧으면 정지 화면이나 반복으로 몰래 채우지 않고 해당 shot을
  실패로 처리한다.
- TTS 자체는 자르거나 속도를 바꾸거나 time-stretch하지 않는다.

### 5.3 AI 통합 제작 방식

AI 통합 방식에서는 별도 TTS를 먼저 생성하지 않는다.

1. shot별 프롬프트에 화자, 나레이션과 인물 대사의 구분, 정확한 화면 자막, 효과음과
   BGM을 명시한다.
2. 생성 비용을 승인받고 AI 통합 영상을 만든다.
3. 실제 파일의 영상·오디오·길이·자막 요구 충족 여부를 검사한다.
4. 준비된 shot을 연결하고 음량을 정규화한 뒤 최종 인코딩한다.

공급자 결과에는 영상과 음성이 하나의 MP4 트랙 조합으로 들어오며 나레이션, 인물 대사,
음악을 나중에 각각 분리해서 편집할 수 있다고 가정하지 않는다.

AI 통합 방식의 최종 길이는 준비된 실제 shot들의 연결 길이다. 목표 길이에 가깝게
생성하되, 말이 없는 안전한 끝부분만 잘라낼 수 있다. 대사나 자막이 잘리거나 계획보다
짧은 경우 time-stretch하지 않고 해당 shot을 재생성 대상으로 표시한다.

## 6. 모델별 provider 계약

### 6.1 Gemini Omni

- 표시 이름: `Gemini Omni`
- API 모델: `gemini-omni-flash-preview`
- Interactions API 사용
- 세로 비율: `response_format.aspect_ratio = "9:16"`
- 생성 단위: 3~10초
- 출력: 720p MP4
- 큰 결과는 `response_format.delivery = "uri"` 사용
- Google 파일이 `ACTIVE`가 될 때까지 확인한 뒤 인증된 download API로 읽는다.

Clipper 방식의 프롬프트에는 장면 묘사와 필요한 ambient/SFX를 적고 다음 금지 조건을
명시한다.

```text
No narration. No character dialogue. No spoken words.
No spoken-word captions or subtitles. No background music.
Render the scene-native visible text requested by the shot prompt.
Ambient sound and scene-appropriate sound effects only.
```

Gemini Omni는 별도의 `generate_audio` 스위치가 아니라 프롬프트로 오디오 내용을
제어한다. 장면 고유 화면 텍스트와 Clipper가 나중에 얹는 대사 자막은 서로 다른
레이어다. 화면 텍스트가 있다고 해서 그 문장을 자동으로 읽는다고 가정하지 않는다.

AI 통합 방식에서는 off-screen narrator와 화면 속 인물의 대사를 명확히 구분하고, 말할
문장과 화면에 표시할 문장을 각각 명시한다. 한국어는 공식적으로 완전 평가된 언어가
아니므로 한국어 음성·자막 정확성 실패도 일반 품질 실패로 처리한다.

### 6.2 Seedance 2.0

- 표시 이름: `Seedance 2.0`
- FAL endpoint: `bytedance/seedance-2.0/text-to-video`
- `resolution = "720p"`
- `aspect_ratio = "9:16"`
- `duration`: 정수 4~15초
- 출력: `video.url`의 MP4

두 제작 방식 모두 환경음이나 통합 음성이 필요하므로 `generate_audio = true`를
사용한다. Clipper 방식에서는 프롬프트로 나레이션·대화·대사를 따라가는 자막·BGM을
금지하되 장면 고유 화면 텍스트는 허용하고, ambient/SFX를 요청한다. AI 통합 방식에서는
말할 문장을 인용해 화자와 립싱크를 지정하고, 화면 자막 요구를 별도로 명시한다.

Seedance의 `generate_audio`는 화면에 보이는 모든 텍스트를 자동으로 읽으라는 뜻이
아니다. 음성 대사와 화면 자막은 독립적인 프롬프트 요구다.

FAL은 장시간 작업이므로 queue `submit`으로 `request_id`를 받은 뒤 상태와 결과를
조회한다. 하나의 사용자 승인당 하나의 provider 생성 요청만 허용한다. 제품이 자체적으로
새 요청을 재제출하는 자동 재시도는 하지 않으며, FAL이 제공하는 retry 비활성화 헤더를
adapter에서 사용해 승인된 호출 수와 실제 호출 수를 맞춘다.

## 7. 기본 `full` 템플릿

### 7.1 원본

원본은 다음 archive branch의 Clipper1 첫 번째 template family다.

```text
desktop/clipper_nestjs
  archive/template-builder-full-2026-06-12
```

정본 catalog row는
`src/project-manifest/catalogs/legacy-clipper1-templates.ko.json`의 `id: 4`,
`template: 1`, `contents_ratio: "full"`이다.

관련 원본 에셋은 archive branch의 다음 파일과 catalog URL을 함께 대조한다.

- `src/projects/assets/clipper-studio-seed/template/layout_legacy_1_full.png`
- `src/projects/assets/legacy-clipper1-template-ui/thumbs-and-origins/1_ratio_full_thumb.png`
- `src/projects/assets/legacy-clipper1-template-ui/thumbs-and-origins/1_ratio_full_origin.png`
- `https://d2x-s3.s3.ap-northeast-2.amazonaws.com/layout/gradient.png`
- `Pretendard-SemiBold.otf`
- `Pretendard-Bold.otf`
- `JalnanGothic.otf`

런타임이 과거 S3 URL에 의존하지 않도록 gradient, thumbnail, origin과 필요한 폰트
파일을 현재 배포 에셋에 포함하고 로컬 URI로 정규화한다.

### 7.2 원본 스타일 값

다음 원본 값을 누락 없이 현재 단일 비율 template variant에 옮긴다.

| 항목 | 값 |
|---|---|
| layout image | `gradient.png` |
| subtitle font / size / color / tracking | `Pretendard-SemiBold.otf` / 40 / `#ffffff` / -1.2 |
| subtitle box | `#000000`, alpha 0.8, height 59, horizontal padding 20 |
| subtitle one-line Y | 1345 |
| subtitle two-line first / second Y | 1310 / 1379 |
| logo font / size / color / tracking | `Pretendard-Bold.otf` / 40 / `#ffffff` / 0 |
| logo text Y | 1658 |
| logo image Y / width / height | 1601 / 800 / 160 |
| sub-title font / size / color / tracking | `JalnanGothic.otf` / 40 / `#ffffff` / -1.2 |
| sub-title one-main-line / two-main-line Y | 228 / 188 |
| main title font / size / colors / tracking | `JalnanGothic.otf` / 80 / `#ffffff` / -4 |
| main title one-line Y | 306 |
| main title two-line first / second Y | 266 / 364 |
| bottom title font / size / color / tracking | `JalnanGothic.otf` / 40 / `#ffffff` / -1.2 |
| bottom title Y | 1494 |
| content area Y | 0 |
| thumbnail | `1_ratio_full_thumb.png` |
| origin | `1_ratio_full_origin.png` |

null인 shadow, outline, border, left/right margin과 title box 값도 null 상태를 보존한다.
현재 변환기가 글자 높이 등 렌더 안전값을 파생하는 경우에는 archive branch의 변환
테스트가 확인한 결과와 golden frame을 기준으로 한다.

### 7.3 현재 template 모델에 등록

- `full` variant 하나만 가진 별도 시스템 family로 등록한다.
- `ownerType = system`, `source = built_in`, `readonly = true`다.
- 사용자는 이 템플릿을 삭제하거나 원본 위에 저장할 수 없다.
- 일반 템플릿 생성 화면의 새 템플릿 비율 선택은 기존 `1:1`, `4:3`만 유지한다.
- Shortform Director의 `Clipper 템플릿 방식`은 이 family와 variant를 자동 선택한다.
- 저장된 프로젝트에는 템플릿 ID뿐 아니라 revision 또는 immutable snapshot을 남겨
  나중의 시스템 템플릿 갱신이 과거 렌더를 바꾸지 않게 한다.

## 8. 로컬 영상 저장과 전송

1차 버전은 S3를 사용하지 않는다. 모든 영구 파일은 기존 local-first 원칙에 따라
`CLIPPER_DATA_DIR` 아래에 둔다.

```text
CLIPPER_DATA_DIR/
  shortform-director/
    projects/<projectId>/
      assets/generated/<shotId>/<revisionId>.mp4
      renders/<renderId>.mp4
```

공급자 결과 전달 순서는 다음과 같다.

```text
Desktop Nest
  → authenticated Web API job endpoint
  → Gemini or FAL
  → Web API authenticated result stream
  → Desktop Nest .part file
  → validate
  → atomic rename to revisionId.mp4
```

Web API는 전체 MP4를 메모리에 올리거나 영구 파일로 저장하지 않고 stream
backpressure를 유지한다. Desktop Nest는 다음 규칙을 적용한다.

- 최대 허용 파일 크기: 256MB
- 임시 확장자: `.part`
- 지원되는 경우 HTTP Range로 중단 지점부터 재개
- Range를 지원하지 않으면 같은 공급자 결과를 처음부터 다시 다운로드
- MIME과 MP4 container 검사
- 9:16, 영상 stream, duration 검사
- 제작 방식에 따른 audio stream 검사
- SHA-256 checksum 계산
- 검증 성공 후 같은 filesystem 안에서 atomic rename

전송 실패는 이미 생성된 공급자 결과의 재다운로드이므로 새 AI 비용을 발생시키지
않는다. 공급자 URL은 임시 위치이며 로컬 파일이 영구 정본이다.

저장 metadata는 다음을 포함한다.

- project, storyboard run, shot, revision ID
- 표시 모델과 실제 API model ID
- 제작 방식과 capability snapshot
- prompt와 요청 길이
- Web API job ID와 provider request/interaction ID
- 공급자 URL은 복구에 필요한 동안만 제한적으로 저장
- 실제 duration, width, height, audio 존재 여부
- byte size, checksum, local relative path
- 생성·다운로드·검증 시각
- 비용과 credential revision snapshot

S3 도입은 cloud render, 여러 기기 동기화, 팀 공유, 원격 백업이 실제 요구가 될 때
별도 설계한다.

## 9. 작업 상태와 복구

각 shot revision은 다음 상태를 가진다.

```text
planned
  → queued
  → generating
  → output_ready
  → downloading
  → ready
```

실패 상태는 단계를 잃지 않도록 구분한다.

- `generation_failed`
- `output_expired`
- `download_failed`
- `validation_failed`
- `quality_failed`
- `cancelled`

공급자 제출이 작업 ID를 만들기 전에 실패해도 해당 shot revision을 계속 `planned`로
남기지 않는다. `generation_failed`로 저장하고 다음의 정규화된 실패 정보만 남긴다.

```text
failure
  code                 # Clipper 공통 실패 코드
  message              # 사용자용 한국어 메시지
  providerStatus?      # 예: 400
  providerCode?        # 예: invalid_request, blocklist
  providerMessage?     # 공급자가 반환한 안전한 짧은 설명
  failedAt
```

Web API는 Gemini와 FAL의 비성공 응답을 JSON 또는 짧은 텍스트로 한 번 읽고,
`providerStatus`, 공급자 오류 코드, 안전한 메시지만 정규화한다. 메시지는 길이를
제한하고 API key, 인증 헤더, 전체 원본 응답, 전체 prompt와 공급자 stack을 저장하거나
Desktop에 전달하지 않는다. 공급자 응답을 해석할 수 없으면 status와 공통 메시지만
남긴다.

Desktop Nest는 이 실패 정보를 로컬 project의 shot job에 영속화한다. 앱을 다시 열어도
마지막 실패 이유를 볼 수 있어야 한다. 사용자가 비용을 다시 승인해 같은 revision을
재제출하고 성공하면 `failure`를 `null`로 만들고 정상 작업 ID와 상태로 대체한다. 이전
실패 원문을 별도 이력으로 무한 축적하지 않는다.

앱 재시작 시 로컬 job ID와 provider request ID로 상태를 재조정한다.

- `queued` / `generating`: Web API와 provider 상태를 다시 확인
- `output_ready` / `downloading`: 같은 결과 다운로드 재개
- `.part`만 존재: checksum·길이 상태를 보고 재개 또는 안전하게 처음부터 다시 전송
- `ready`: 로컬 파일을 다시 검사하고 누락됐으면 `download_failed`로 되돌림

한 shot이 실패해도 이미 성공한 다른 shot은 유지한다. 모든 필수 shot이 `ready`가 된
경우에만 최종 렌더를 활성화한다.

사용자 승인이 필요한 생성·품질 실패에는 자동으로 새 provider 요청을 만들지 않는다.
provider 작업 ID가 만들어진 뒤 실패한 작업의 `재생성`은 해당 shot의 추가 예상 비용을
보여주고 승인 뒤 새 revision을 만든다. 이전 revision과 lineage는 삭제하지 않는다.
provider 작업 ID가 만들어지기 전 제출 실패만 같은 revision과 idempotency key로 다시
제출할 수 있다.

공급자 제출 전 실패는 동일 입력의 수동 재시도로 성공할 수 있지만 제품이 자동으로
재호출하지 않는다. 화면은 다음처럼 원인과 행동을 구분한다.

- `blocklist` 또는 명시적 정책 거절: 프롬프트를 바꿔 다시 생성하도록 안내
- `invalid_request` / `parameter_unknown`: 입력 또는 공급자 계약을 점검하도록 안내
- 상세 코드 없는 HTTP 400: 공급자가 요청을 거절했으며 같은 비용 승인으로 다시
  제출할 수 있음을 안내
- 401 / 403: 자격 증명 또는 유료 사용 설정 확인
- 429: 할당량 또는 사용 한도 확인
- 5xx: 일시적 공급자 장애로 안내

## 10. 품질 검증

공통 기계 검증은 다음을 포함한다.

- MP4가 열리는지
- 영상 stream이 존재하는지
- 해상도와 9:16 비율이 맞는지
- 실제 길이가 계획을 충족하는지
- 파일 크기와 checksum이 기록됐는지
- 필요한 제작 방식에서 audio stream이 존재하는지

Clipper 템플릿 방식에서는 기존 로컬 STT/음성 검사를 재사용해 AI 원본에서 알아들을 수
있는 사람 말소리가 감지되는지 확인한다. 나레이션이나 인물 대사가 감지되면
`quality_failed`다. 음원 분리로 억지로 제거하지 않고 사용자 승인 뒤 해당 shot을 다시
생성한다.

AI 통합 방식에서는 프롬프트가 요구한 대사·자막의 완전한 자동 판정을 보장할 수 없다.
가능한 STT/OCR 검사는 경고 근거로 사용하고, shot 미리보기에서 사용자가 최종 확인할
수 있게 한다. 명백한 누락은 개별 shot 재생성 대상으로 표시한다.

## 11. 최종 렌더와 오디오

### 11.1 Clipper 템플릿 방식

렌더 순서는 다음과 같다.

1. 720×1280 AI 영상을 1080×1920으로 비율 변경 없이 확대
2. 필요 구간 trim과 짧은 SFX tail fade
3. `full` gradient와 템플릿 레이아웃 합성
4. TTS 타임스탬프 기준의 정확한 자막 오버레이
5. Clipper TTS 합성
6. AI ambient/SFX 정규화
7. 사용자가 BGM을 선택한 경우 Clipper BGM 추가와 TTS 구간 ducking
8. 1080×1920 최종 MP4 인코딩

믹스 우선순위는 TTS, AI 환경음·효과음, 선택된 Clipper BGM 순이다. TTS가 가장
명확해야 하고 BGM이 있으면 가장 낮으며 TTS 구간에서 더 줄어든다. 기존 Clipper
렌더러의 검증된 mix preset을 재사용하고 이번 기능만을 위한 새 임의 음량 상수를 여러
곳에 만들지 않는다.

최종 duration은 실제 TTS timeline과 정확히 일치한다.

### 11.2 AI 통합 제작 방식

- Clipper 템플릿, Clipper TTS, Clipper 자막을 추가하지 않는다.
- provider MP4의 혼합 오디오를 유지한다.
- shot 경계의 음량 차이를 정규화하고 필요한 짧은 crossfade만 적용한다.
- 말이 없는 안전한 끝부분 외에는 대사 트랙을 자르지 않는다.
- 1080×1920으로 확대·연결·최종 인코딩한다.

## 12. 비용

비용은 `예상`과 `실제 또는 사후 추정`을 구분한다.

### 12.1 승인 지점

1. 스토리보드 LLM 호출 전
2. 전체 shot 영상 생성 전
3. 실패 shot 개별 재생성 전

전체 shot 승인 화면은 선택 모델, shot 수, 요청 초 합계와 예상 USD를 한 번에 보여준다.
이미 승인된 범위를 넘는 생성 요청은 만들지 않는다.

### 12.2 2026-08-05 가격 snapshot

| 모델 | 계산 기준 |
|---|---|
| Gemini Omni | 720p 영상 약 USD 0.10/초. 실제 청구는 output token 기준이며 720p 1초당 5,792 tokens |
| Seedance 2.0 | 720p text-to-video USD 0.3034/초 |

Seedance의 `generate_audio` on/off는 같은 가격이다. 가격은 provider가 바꿀 수 있으므로
화면과 여러 adapter에 숫자를 복제하지 않고 Web API의 날짜·출처가 있는 가격 catalog에서
계산한다.

provider가 실제 usage를 주면 그 값을 사용한다. 주지 않는 경우 요청 길이 또는 실제 결과
길이와 snapshot 단가로 계산하고 `사후 추정`이라고 표시한다. 호출별, shot별,
스토리보드 전체 합계를 확인할 수 있어야 한다.

다운로드 재시도와 로컬 최종 렌더는 provider 영상 생성 비용을 새로 발생시키지 않는다.

## 13. 화면 흐름

### 13.1 프로필

기존 프로필 생성·수정 폼에 숫자 필드 하나를 추가한다.

```text
목표 영상 길이(초)  [ 30 ]
15~60초 사이의 정수를 입력하세요.
```

### 13.2 스토리보드 설정

영상 후보 카드의 `스토리보드 만들기`에서 설정 화면을 먼저 연다.

- 영상 모델 카드 2개
- 제작 방식 카드 2개
- 현재 목표 길이
- 모델별 shot 최대 길이와 예상 shot 수
- 스토리보드 예상 비용
- `스토리보드 만들기`

모델명은 API ID가 아니라 `Gemini Omni`, `Seedance 2.0`으로 표시한다. API ID와
credential revision은 접힌 기술 정보에 둔다.

### 13.3 스토리보드와 생성

스토리보드 화면은 장면과 내부 shot을 순서대로 보여준다. 사용자가 승인한 다음
`영상 만들기`를 누르면 전체 생성 예상 비용을 표시한다.

Clipper 방식에서만 기존 narration preset·속도 선택과 BGM 선택을 보여준다. narration
preset은 필수이고 BGM은 `선택 안 함`이 가능하다. AI 통합 방식에서는 이 영역을
표시하지 않는다.

영상 생성이 시작된 뒤 목소리나 속도를 바꾸면 새 production revision과 추가 영상 비용이
필요할 수 있음을 변경 전에 보여준다. BGM 변경은 최종 렌더만 다시 필요하다고 표시한다.

shot 카드 상태:

- 생성 대기
- 생성 중
- 결과 받는 중
- 준비 완료
- 실패

각 준비 완료 shot은 미리볼 수 있다. 실패 카드에는 사람이 이해할 수 있는 이유,
비용 없는 `다운로드 다시 시도` 또는 비용이 드는 `재생성` 중 맞는 행동만 표시한다.
공급자 제출 실패에는 정규화된 공급자 코드·메시지를 표시하며 앱 재시작 뒤에도
유지한다. 재시도가 성공하면 이전 실패 표시는 제거한다.

### 13.4 최종 결과

- 최종 렌더 진행 상태
- 완성 영상 미리보기
- 실제 또는 사후 추정 비용 합계
- 로컬 파일 위치 열기
- 개별 shot 재생성 후 최종 영상 다시 만들기

## 14. API와 계약 원칙

- Web API의 공개 계약 변경은
  `web/clipper_web_api/docs/api/openapi.yaml`을 먼저 수정한다.
- 성공 응답은 기존 raw response 원칙을 유지한다.
- provider별 응답을 Angular에 직접 노출하지 않고 공통 job·cost·media metadata로
  정규화한다.
- provider 오류도 status·code·안전한 message만 공통 실패 계약으로 정규화하고 raw
  response와 credential은 공개 응답에 포함하지 않는다.
- job 제출은 client idempotency key를 받아 중복 클릭과 재시작으로 같은 유료 작업이
  두 번 생성되지 않게 한다.
- 자격 증명은 Web API에서만 해석하며 Desktop과 Angular에는 provider key를 반환하지
  않는다.

## 15. 검증

유료 provider E2E를 제외한 자동 검증은 mock provider와 작은 로컬 MP4 fixture로 한다.

### 15.1 계약·도메인

- 기존 프로필의 30초 기본값과 15~60 정수 검증
- 모델·제작 방식·capability snapshot 저장
- Omni 3~10초, Seedance 4~15초 shot validator
- 모델·제작 방식 변경 시 스토리보드 재생성 요구
- 영상 생성 뒤 TTS 목소리·속도 변경 시 새 production revision 요구
- BGM 변경 시 provider 영상을 재사용하는지
- idempotency와 revision lineage

### 15.2 템플릿

- archive template 1 full의 모든 원본 필드 mapping
- gradient, thumbnail, origin, 세 폰트의 패키지 포함
- 시스템 readonly와 단일 `full` variant
- 일반 새 템플릿 비율이 계속 `1:1`, `4:3`뿐인지
- golden frame으로 archive full 렌더와 현재 렌더 비교

### 15.3 provider와 파일

- Gemini URI 결과의 ACTIVE 확인과 stream
- FAL queue 상태와 `video.url` 결과
- provider key가 client에 노출되지 않는지
- 256MB 제한, MIME/container/ratio/duration 검증
- `.part` 다운로드, 중단 재개, atomic rename, checksum
- 앱 재시작 뒤 job 복구
- 전송 실패가 새 생성 요청을 만들지 않는지
- 생성·품질 실패 재생성에 새 승인이 필요한지
- 공급자 비성공 응답의 안전한 코드·메시지만 전달되고 secret·raw body·prompt가
  노출되지 않는지
- 공급자 제출 실패가 `generation_failed`로 저장되고 앱 재시작 뒤 복원되는지
- 같은 revision의 수동 재시도가 성공하면 이전 실패가 제거되는지

### 15.4 렌더

- 720×1280에서 1080×1920으로 crop 없는 확대
- TTS 실제 길이와 최종 duration 일치
- 기존 narration preset·속도 snapshot과 선택적 BGM 적용
- 소수 TTS 길이에 대한 provider 길이 올림·영상 trim
- 정확한 TTS 자막 타임스탬프
- TTS, AI ambient/SFX, 선택된 Clipper BGM mix와 ducking
- AI 통합 방식에 템플릿·별도 TTS·자막이 중복되지 않는지
- 최종 MP4 재생과 로컬 결과 metadata

### 15.5 UI

- 목표 길이 생성·수정
- 스토리보드 전 모델·제작 방식 선택
- 비용 승인 전 호출이 발생하지 않는지
- shot별 진행·부분 성공·실패·재생성
- 공급자 오류 코드·사람이 읽는 메시지와 적절한 다음 행동
- 재시작 후 진행 상태 복원
- 최종 미리보기와 로컬 위치 열기

각 저장소의 직접 영향 테스트, 전체 관련 suite, production build를 수행한다. 실제
Gemini와 FAL의 유료 smoke test는 구현 자동 검증에 포함하지 않으며, 모델·shot 길이·예상
비용을 다시 제시하고 사용자의 별도 승인을 받은 뒤 각 모델의 최소 1 shot만 실행한다.

## 16. 비범위

- S3 또는 다른 cloud object storage
- 여러 기기 간 생성 파일 동기화
- 팀 공동 프로젝트와 원격 렌더
- AI 통합 결과에서 음성·음악·효과음을 stem으로 분리
- AI 영상 속 잘못된 자막을 후처리로 완벽히 수정
- 일반 사용자가 새 `full` 템플릿을 만드는 기능
- 영상 공식을 별도 catalog로 만드는 기능
- Shorts 정밀 분석 플러그인
- 선택한 조사 주제의 댓글을 추가 분석하는 기능

## 17. 공식 참고 자료

2026-08-05에 확인했다. preview 모델과 가격은 구현 및 유료 E2E 직전에 다시 확인한다.

- [Gemini Omni Flash 생성·오디오·텍스트·URI 전달](https://ai.google.dev/gemini-api/docs/omni)
- [Gemini API 가격](https://ai.google.dev/gemini-api/docs/pricing)
- [Gemini API 변경 기록](https://ai.google.dev/gemini-api/docs/changelog)
- [FAL Seedance 2.0 text-to-video API](https://fal.ai/models/bytedance/seedance-2.0/text-to-video/api)
- [FAL Seedance 2.0 모델·가격](https://fal.ai/models/bytedance/seedance-2.0/text-to-video)
- [FAL 비동기 queue 계약](https://fal.ai/docs/documentation/model-apis/inference/queue)
