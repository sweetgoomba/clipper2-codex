# AI 숏폼 디렉터 제작 모델 선택·장면 편집 설계

- 작성일: 2026-07-28
- 상태: 사용자 승인
- 정본 위치: `.codex/design/SHORTFORM_DIRECTOR_PRODUCTION_MODEL_AND_SCENE_REVISION_DESIGN_2026-07-28.md`
- 관련 문서:
  - `.codex/design/2026-07-27-shortform-director-quality-input-lineage-and-production-design.md`
  - `.codex/design/2026-07-27-shortform-director-quality-input-production-implementation-plan.md`

## 1. 결정 배경

기존 계획에는 대표 생성 영상 장면을 Omni와 Veo로 각각 만들어 비교하는 전용 기능이
포함되어 있었다. 이 기능은 최종 사용자가 영상을 제작하는 데 필요한 기능이 아니라
개발 과정의 모델 평가 도구에 가깝다.

AI 숏폼 디렉터를 먼저 완성하고 실제 제작 과정에서 모델 품질을 비교할 수 있도록 다음과
같이 방향을 바꾼다.

1. 생성 영상의 초기 기본 모델은 `gemini-omni-flash-preview`로 정한다.
2. 별도의 Omni/Veo 비교 화면과 비교 실행 API는 만들지 않는다.
3. 실제 영상 제작 화면에서 장면별 제작 방식과 모델을 바꿀 수 있게 한다.
4. 장면을 다시 만들 때 이전 결과를 덮어쓰지 않고 제작 이력으로 남긴다.
5. 동일 장면을 다른 모델로 다시 만들어 실제 제품 안에서 결과를 비교한다.
6. 특정 모델이나 공급자에 고정되지 않는 능력 기반 모델 목록을 사용한다.

## 2. 목표

- 영상 제작 페이지에서 현재 사용되는 기본 모델과 제작 도구를 확인할 수 있다.
- 각 장면의 실제 시각 레이어마다 제작 방식을 변경할 수 있다.
- AI 이미지·AI 영상을 선택한 경우 사용 가능한 모델을 선택할 수 있다.
- 한 장면만 변경했을 때 변경하지 않은 장면의 기존 파일을 재사용할 수 있다.
- 장면을 다시 만들어도 이전 결과와 제작 정보를 계속 확인할 수 있다.
- 완성된 모든 영상은 다시 편집하고 새 버전으로 렌더할 수 있다.
- 새 공급자나 모델을 추가할 때 화면과 프로젝트 계약을 다시 설계하지 않는다.
- 모든 설정, 호출, 결과, 버전 연결 정보는 기존 로컬 JSON 저장 구조에 남는다.
- 실제 외부 호출은 기존 관리자 credential과 Web API 경계를 통해서만 실행한다.

## 3. 비목표

이번 구현에서 다음은 하지 않는다.

- 전역 기본 모델을 사용자가 수정하는 설정 화면
- 별도의 개발자용 A/B 비교 페이지
- 실제 API 연결이 없는 모델을 선택 가능한 항목으로 노출
- Seedance, Higgsfield 등 신규 공급자의 API·credential 연결
- API key를 Electron 또는 데스크톱 로컬 JSON에 저장
- AI Director 크레딧 차감
- Remotion 도입 또는 대체 렌더러 언급

전역 기본값 편집과 신규 공급자 연결은 TODO로 남긴다. 다만 이번 계약은 공급자 추가를
수용할 수 있어야 한다.

## 4. 검토한 접근

### 4.1 비교 전용 기능 유지

대표 장면을 Omni와 Veo로 생성하고 winner를 고른다.

- 장점: 내부 실험 결과를 빠르게 한 화면에서 볼 수 있다.
- 단점: 최종 제품에서 쓰지 않을 전용 API·화면·상태가 생긴다.
- 결정: 제외한다.

### 4.2 Omni 고정 후 나중에 일반화

현재 생성 영상은 모두 Omni로 만들고 모델 선택 기능을 뒤로 미룬다.

- 장점: 첫 구현량이 가장 작다.
- 단점: 장면 편집과 신규 공급자 추가 시 계약을 다시 뜯어고쳐야 한다.
- 결정: 제외한다.

### 4.3 능력 기반 모델 목록과 장면별 override

작업 종류별 기본값과 사용 가능한 구현을 모델 목록으로 제공하고, 프로젝트와 장면은
선택값의 snapshot을 보존한다.

- 장점: 실제 제품 기능으로 모델을 바꾸고 비교할 수 있다.
- 장점: Omni, Veo, Seedance, 외부 집계 서비스 등을 같은 UI 계약으로 추가할 수 있다.
- 장점: 장면별 제작 이력과 비용 추적에 자연스럽게 연결된다.
- 단점: 고정 문자열 두 개보다 초기 계약이 조금 더 필요하다.
- 결정: 이 방식을 채택한다.

## 5. 핵심 용어

### 5.1 제작 능력(capability)

모델 이름이 아니라 수행할 작업을 뜻한다.

- `research.query-plan`
- `research.source-normalization`
- `research.youtube-analysis`
- `content.topic-synthesis`
- `content.candidate-generation`
- `production.video-plan`
- `production.scene-media-decision`
- `media.image-generation`
- `media.video-generation`
- `audio.narration`
- `render.final-composition`

### 5.2 제작 구현(production implementation)

한 제작 능력을 실제로 수행하는 provider와 model 또는 tool 조합이다.

예:

- `google_ai / gemini-omni-flash-preview`
- `google_ai / veo-3.1-fast-generate-preview`
- `naver / image-search`
- `local / motion-canvas`
- `local / tts.supertone`

### 5.3 기본값(default)

해당 능력에서 별도 override가 없을 때 사용하는 구현이다. 이번 구현에서는 코드로
관리하고 읽기 전용으로 노출한다.

### 5.4 override

특정 프로젝트 또는 특정 시각 레이어에서 기본값 대신 선택한 구현이다. 최초 구현은
장면의 시각 레이어별 override만 제공한다.

### 5.5 장면과 레이어

사용자에게는 장면 단위로 보여주지만 실제 미디어 생성·검색·교체 단위는 장면 안의
시각 레이어다. 한 장면에 배경, 제품, 증거 자료가 함께 있을 수 있으므로 변경 API와
이력은 `sceneId + layerId`로 식별한다.

## 6. 초기 기본값

현재 코드와 승인된 방향을 기준으로 다음 값을 표시한다.

| 제작 능력 | Provider | 기본 구현 |
|---|---|---|
| 조사 질문 계획 | OpenAI | `gpt-5.4-nano` |
| 조사 자료 정규화 | OpenAI | `gpt-5.4-nano` |
| YouTube 참고 영상 분석 | Google AI | `gemini-3.6-flash` |
| 주제 종합 | OpenAI | `gpt-5.6-luna` |
| 영상 후보 생성 | OpenAI | `gpt-5.6-luna` |
| 상세 영상 계획 | OpenAI | `gpt-5.6-luna` |
| 장면 미디어 결정 | OpenAI | `gpt-5.6-luna` |
| AI 이미지 생성 | Google AI | `gemini-3.1-flash-image` |
| AI 영상 생성 | Google AI | `gemini-omni-flash-preview` |
| 내레이션 | Local | `tts.supertone` |
| 최종 합성 | Local | `motion-canvas` |

`gpt-4.1`은 기존 결과 비교용 baseline으로만 남고 새 프로젝트의 기본값으로 표시하지
않는다.

첫 구현의 선택 가능한 AI 영상 모델은 실제 호출 코드가 존재하는 다음 두 개다.

- `gemini-omni-flash-preview` — 기본
- `veo-3.1-fast-generate-preview`

첫 구현의 선택 가능한 AI 이미지 모델은 실제 호출 코드가 존재하는
`gemini-3.1-flash-image` 하나다. 선택지가 하나여도 실제 사용 모델과 향후 확장 위치를
명확히 하기 위해 표시한다.

## 7. 모델 목록 계약

화면은 provider별 하드코딩 분기를 만들지 않고 다음 안전한 공개 정보만 받는다.

```ts
interface ProductionCapabilityCatalogV1 {
  schemaVersion: 'production-capability-catalog.v1';
  generatedAt: string;
  capabilities: ProductionCapabilityEntryV1[];
}

interface ProductionCapabilityEntryV1 {
  capabilityId: string;
  label: string;
  defaultImplementationId: string;
  implementations: ProductionImplementationV1[];
}

interface ProductionImplementationV1 {
  id: string;
  providerId: string;
  modelId: string | null;
  label: string;
  selectable: boolean;
  ready: boolean;
  unavailableReason: 'credential_missing' | 'not_connected' | null;
}
```

- `selectable`은 제품이 해당 조합을 허용하는지를 뜻한다.
- `ready`는 현재 활성 credential 등 실제 실행 조건이 준비되었는지를 뜻한다.
- API key 값은 절대 포함하지 않는다.
- credential ID와 revision은 실행 승인·audit에만 사용하고 기본 목록 화면에서는
  필요할 때만 안전한 식별값으로 표시한다.

텍스트 추론의 기존 allowlist와 생성 미디어의 기존 허용 모델을 이 계약 뒤에서
재사용한다. 동일한 모델 목록을 Angular, Nest, Web API 세 곳에 각각 복제하지 않는다.

소유권은 다음처럼 고정한다.

- `clipper_web_api`: 외부 credential이 필요한 추론·생성 provider, 허용 모델, 외부 작업의
  기본 구현
- `clipper_nestjs`: Web API 목록에 Supertonic·Motion Canvas 같은 로컬 구현을 합성하고
  프로젝트에 사용된 catalog snapshot 저장
- `clipper_angular`: Nest가 반환한 목록만 표시하고 선택값을 implementation ID로 전달

현재 Web API의 `videoModel: 'omni' | 'veo-fast'` 분기는 범용 implementation ID로
치환한다. Web API는 요청된 implementation ID와 실제 provider 응답 model ID가 일치하는지
계속 검증한다.

## 8. 화면 설계

### 8.1 영상 제작 페이지 상단

`현재 제작 모델` 접이식 요약을 둔다.

- 기본 상태에서는 역할, provider, model을 간단히 보여준다.
- 펼치면 전체 능력 목록과 현재 실행 준비 여부를 확인할 수 있다.
- 전체 기본값 수정 버튼은 만들지 않는다.
- “기본값 변경 기능은 추후 제공” 문구만 표시한다.
- credential이 없는 구현은 `설정 필요`로 표시하되 API key 값을 노출하지 않는다.

### 8.2 장면 카드

현재 장면 계획 카드에 각 시각 레이어의 다음 정보를 추가한다.

- 역할과 장면 내 위치
- 현재 제작 방식
- 현재 선택한 provider와 model 또는 tool
- 현재 사용 중인 결과 파일과 revision
- `제작 정보`
- `편집`
- `다시 만들기`

장면 자체의 편집에서는 다음을 수정할 수 있다.

- 내레이션 문구
- 화면에 표시되는 자막·라벨·CTA 문구
- 시각 레이어의 제작 방식
- 검색어 또는 생성 prompt
- AI 생성 모델

이번 범위는 기존 장면의 내용을 수정하는 편집이다. 프레임 단위 타임라인 편집과 장면
추가·삭제·순서 변경은 후속 편집기 범위로 둔다.

### 8.3 장면 레이어 편집

제작 방식 dropdown은 다음 값을 제공한다.

- 조사 자료 사용(`source`)
- 네이버 이미지 검색(`search`)
- AI 이미지 생성(`generated-image`)
- AI 영상 생성(`generated-video`)
- 코드 기반 도식(`programmatic`)

현재 구현에서 실제로 지원하지 않는 방식은 선택지에 노출하지 않는다. 기존의 `owned`는
보유 파일 우선 전략으로 사용하지 않으며 이번 편집 선택지에서 제외한다.

선택한 방식에 따라 입력을 바꾼다.

| 제작 방식 | 추가 입력 |
|---|---|
| 조사 자료 | 사용 가능한 근거 자료 선택 |
| 네이버 이미지 검색 | 검색어, 선택 결과, 권리 확인 |
| AI 이미지 생성 | prompt, 이미지 모델 |
| AI 영상 생성 | prompt, 영상 모델 |
| 코드 기반 도식 | 도식 내용과 지원되는 primitive |

AI 모델 dropdown은 선택한 capability의 `selectable` 구현만 보여준다. `ready=false`인
항목은 이유를 표시하고 실행할 수 없게 한다.

### 8.4 제작 정보

장면 레이어별 `제작 정보`에서 다음 내용을 확인한다.

- 제작 방식
- provider와 model 또는 tool
- prompt 또는 검색어
- 연결된 조사 자료와 근거 ID
- 생성 시각
- credential revision 식별값
- provider request ID
- 입력 fingerprint
- 결과 artifact ID, media type, checksum, 파일 크기
- 이전 revision과 다음 revision의 연결
- 관련 호출 audit artifact

### 8.5 완성 영상 편집

결과물 상세에서 `이 영상 편집`을 선택하면 원본 AI Director project ID를 유지한 채
영상 제작 페이지로 돌아간다.

- 특정 레이어만 수정할 수 있다.
- 특정 장면의 내레이션과 화면 문구를 수정할 수 있다.
- 여러 레이어를 수정한 뒤 한 번에 최종 렌더를 다시 요청할 수 있다.
- `전체 다시 만들기`는 모든 생성·검색 레이어를 새 revision으로 만든다.
- 각 최종 렌더는 새 output revision을 만들며 기존 MP4를 덮어쓰지 않는다.

## 9. 장면 미디어 revision

현재 `AssetAcquisitionV1`의 단일 결과와 attempt 숫자만으로는 이전 결과를 충분히
보존할 수 없다. 활성 binding은 그대로 두고 별도의 append-only revision 기록을
추가한다.

```ts
interface SceneMediaRevisionV1 {
  schemaVersion: 'scene-media-revision.v1';
  id: string;
  projectId: string;
  sceneId: string;
  layerId: string;
  parentRevisionId: string | null;
  status: 'queued' | 'running' | 'succeeded' | 'failed' | 'cancelled';
  strategy: 'source' | 'search' | 'generated-image' | 'generated-video' | 'programmatic';
  implementation: {
    capabilityId: string | null;
    implementationId: string | null;
    providerId: string | null;
    modelId: string | null;
    credentialRevision: string | null;
  };
  request: {
    brief: string;
    prompt: string | null;
    searchQuery: string | null;
    sourceIds: string[];
  };
  inputFingerprint: string;
  result: {
    assetRefId: string;
    artifactId: string;
    mediaType: string;
    sizeBytes: number;
    checksum: string;
  } | null;
  failure: {
    code: string;
    retryable: boolean;
    message: string | null;
  } | null;
  auditArtifactIds: string[];
  createdAt: string;
  completedAt: string | null;
}
```

`programmatic`은 provider 호출과 별도 binary가 없으므로 성공 revision의 `result`가
`null`일 수 있다. 이때 layer의 programmatic payload snapshot이 결과 근거다.

검색 파일 준비에 성공했지만 권리 확인이 끝나지 않은 경우에도 revision 자체는
`succeeded`로 보존한다. 다만 활성 pointer와 render binding은 바꾸지 않고, 사용자가
권리를 확인한 뒤 해당 revision을 활성화한다.

프로젝트에는 레이어별 활성 revision만 가리키는 작은 index를 둔다.

```ts
interface ActiveSceneMediaRevisionV1 {
  layerId: string;
  revisionId: string;
}
```

실제 revision 본문은 프로젝트 JSON 하나를 계속 키우지 않도록 기존 실행별 로컬 JSON
artifact 저장 패턴을 따른다. 프로젝트 JSON에는 활성 포인터와 요약만 둔다.

내레이션 문구를 바꾸면 해당 cue의 TTS artifact도 새 revision으로 만든다. 성공한 이전
TTS artifact는 보존한다. 새 음성 길이를 측정한 뒤 기존 TTS timing alignment를 다시
실행하므로 이후 장면의 시작 시각은 바뀔 수 있지만, 변경하지 않은 시각 media artifact는
다시 생성하지 않는다.

## 10. 변경·재생성 규칙

### 10.1 설정만 변경

사용자가 제작 방식, prompt, 검색어 또는 모델을 변경하면 아직 기존 결과를 삭제하지
않는다. 편집 초안과 현재 활성 revision을 함께 보여준다.

### 10.2 특정 레이어 다시 만들기

1. 현재 project revision, layer 설정, credential revision, 예상 호출 수와 비용을
   계산한다.
2. 사용자에게 실제 호출 전 승인 정보를 보여준다.
3. 승인된 fingerprint와 현재 입력이 같을 때만 실행한다.
4. 새 `SceneMediaRevisionV1`을 만든다.
5. 성공하면 새 asset ref를 만든 뒤 해당 레이어 binding을 새 결과로 전환한다.
6. 실패하면 기존 활성 binding을 유지한다.
7. 이전 revision과 실패 revision을 모두 보존한다.

### 10.3 변경하지 않은 레이어

입력 fingerprint가 같고 기존 artifact가 실제로 존재하며 checksum이 일치하면 그대로
재사용한다. 다시 검색하거나 생성하지 않는다.

### 10.4 최종 영상 다시 렌더

활성 장면 revision과 내레이션 artifact를 사용해 새 render recipe를 만들고 기존 보관함
큐에 새 작업으로 넣는다. 보관함 파일은
`renders/revisions/<renderRevisionId>/main.mp4`에 no-replace로 게시해 기존 MP4와 기존
큐 기록을 삭제하거나 덮어쓰지 않는다.

## 11. API 경계

Angular는 기존처럼 로컬 Nest API만 호출한다. Nest는 현재 사용자와 project ownership을
검증하고, credential이 필요한 외부 호출만 Web API로 전달한다.

초기 계약은 다음 책임으로 나눈다.

### 11.1 제작 목록

- `GET /projects/shortform-director/production-capabilities`
  - 안전한 모델·도구 목록과 현재 준비 상태 반환

### 11.2 장면 편집

- `PATCH /projects/shortform-director/projects/:projectId/scenes/:sceneId`
  - 내레이션과 화면 문구 편집
  - 외부 호출 없음
- `PATCH /projects/shortform-director/projects/:projectId/scenes/:sceneId/layers/:layerId`
  - 제작 방식, prompt/search query, implementation override 저장
  - 외부 호출 없음

### 11.3 장면 재생성

- `GET /projects/shortform-director/projects/:projectId/scenes/:sceneId/layers/:layerId/regeneration-preflight`
  - 실제 provider, model, credential revision, 호출 수, 예상 비용, approval ID 반환
- `POST /projects/shortform-director/projects/:projectId/scenes/:sceneId/layers/:layerId/regenerations`
  - 승인 fingerprint 검증 후 해당 레이어만 실제 준비
- `GET /projects/shortform-director/projects/:projectId/scenes/:sceneId/layers/:layerId/revisions`
  - 이전 결과와 실패 이력 조회
- `POST /projects/shortform-director/projects/:projectId/scenes/:sceneId/layers/:layerId/revisions/:revisionId/activate`
  - 과거 성공 revision을 새 호출 없이 다시 활성화
- `GET /projects/shortform-director/projects/:projectId/scenes/:sceneId/narration-regeneration-preflight`
  - 변경된 cue의 TTS 호출·timing 재정렬 범위 확인
- `POST /projects/shortform-director/projects/:projectId/scenes/:sceneId/narration-regenerations`
  - 변경된 cue만 새 TTS artifact로 만들고 timing alignment 갱신

### 11.4 전체 재생성

전체 다시 만들기는 별도 provider 비교 API가 아니라 각 변경 대상 레이어의 준비 작업을
하나의 사용자 작업으로 묶는다. 각 외부 호출과 결과는 여전히 레이어 revision으로
기록한다.

## 12. 저장 위치와 audit

다음 데이터는 기존 `CLIPPER_DATA_DIR` 기반 로컬 JSON 저장소와 artifact repository를
사용한다.

- production capability catalog snapshot
- 프로젝트가 사용한 기본값 snapshot
- 레이어 편집 초안
- scene media revision
- provider 호출 입력의 필요한 구조화 데이터
- 파싱·검증된 provider 응답
- token·비용·지연·provider request ID
- 생성 파일의 checksum과 상대경로
- render revision과 사용한 scene media revision ID

응답 전체 원문을 `raw` 같은 금지 필드로 저장하지 않는다. 필요한 구조화 필드와
파싱된 결과만 저장한다. API key와 secret header는 저장하지 않는다.

## 13. 신규 공급자 확장

Seedance, Higgsfield 또는 다른 집계 서비스를 추가할 때 다음만 추가한다.

1. 관리자 credential 종류와 테스트
2. Web API provider adapter
3. 허용 모델과 capability 목록
4. 비용 계산 정책
5. 실제 media 결과를 공통 generated media 결과로 변환하는 mapper

Angular 장면 편집 화면과 프로젝트 revision 계약은 변경하지 않는다.

신규 공급자는 실제 credential 등록과 실호출 검증이 끝난 뒤에만 `selectable=true`로
노출한다.

## 14. 오류 처리

- credential 누락: 모델은 목록에 보이지만 실행 불가와 설정 필요 이유를 표시한다.
- stale approval: project, layer 입력, 모델, credential revision 중 하나라도 바뀌면
  실행하지 않고 새 preflight를 요구한다.
- provider 반환 model 불일치: 결과를 활성화하지 않고 실패 revision으로 남긴다.
- 검색 결과 권리 미확인: 렌더 가능한 활성 binding으로 전환하지 않는다.
- 생성 실패: 기존 성공 revision과 현재 최종 영상은 유지한다.
- artifact 유실 또는 checksum 불일치: 재사용하지 않고 다시 준비가 필요하다고 표시한다.
- 지원하지 않는 방식·모델 조합: 저장 단계에서 거부한다.

## 15. 기존 비교 스캐폴드 처리

다음 비교 전용 개념은 범용 계약으로 대체한 뒤 제거한다.

- `ShortformDirectorVideoModelProfile = 'omni' | 'veo-fast'`
- `video-model-comparison` 전용 Angular service, gateway, store, fixture
- 대표 장면 자동 선택
- 비교 전용 preflight, run, selection route 기대값
- production page의 오래된 Veo/Imagen fixture 기대값

기존 실제 provider 호출 코드는 제거하지 않는다. Omni와 Veo adapter는
`media.video-generation` 구현으로 재사용한다.

## 16. 구현 순서

1. 범용 production capability 계약과 현재 기본값 endpoint
2. 영상 제작 페이지 상단의 읽기 전용 기본 모델 요약
3. scene media revision repository와 프로젝트 활성 포인터
4. 장면 문구·레이어 제작 설정 편집 계약과 UI
5. 단일 레이어 preflight·실제 재생성·이력 조회
6. 장면 내레이션 재합성·timing alignment
7. 과거 revision 활성화와 변경하지 않은 artifact 재사용
8. 완성 영상에서 편집으로 돌아오는 흐름과 새 render revision
9. 비교 전용 Angular 스캐폴드 제거
10. 전체 다시 만들기
11. 실제 credential을 사용한 승인 기반 E2E 검증

외부 유료 호출이 필요한 11단계에서는 호출할 provider, model, 횟수, 예상 비용을 먼저
사용자에게 알리고 별도 승인을 받은 뒤 실행한다.

## 17. 검증 기준

- 기본 AI 영상 모델이 Omni로 표시되고 실제 preflight에도 같은 model ID가 나온다.
- 생성 영상 장면에서 Omni와 Veo Fast를 선택할 수 있다.
- 코드 도식에는 AI 모델이 표시되지 않고 제작 도구만 표시된다.
- 네이버 이미지 장면에는 모델 대신 검색 provider, 검색어, source URL이 남는다.
- 한 레이어의 모델을 바꿔도 다른 레이어 artifact ID와 checksum이 유지된다.
- 재생성 성공 전에는 기존 활성 장면 결과가 유지된다.
- 재생성 성공 후 이전 revision과 새 revision을 모두 조회할 수 있다.
- 과거 성공 revision을 활성화할 때 provider를 다시 호출하지 않는다.
- 장면 내레이션을 수정하면 해당 cue만 다시 합성되고 새 음성 길이로 timing이 정렬된다.
- 최종 재렌더가 기존 보관함 큐로 들어가고 기존 MP4를 덮어쓰지 않는다.
- 생성·검색·추론 audit JSON에서 사용 모델과 근거를 역추적할 수 있다.
- runtime production 코드에 fixture 또는 가짜 provider 응답이 없다.
- AI Director 경로에 크레딧 조회·차감이 없다.

## 18. 후속 TODO

- 전역 기본 모델 편집과 조직별 정책
- Seedance API 또는 이를 제공하는 service adapter 검토
- Higgsfield 등 다중 모델 service adapter 검토
- 이미지 생성 모델 추가
- 모델별 가격표 자동 갱신
- 장면 revision 간 나란히 미리보기
- 결과 품질 평가 점수와 사용자 선택 이유 기록
- 장면 추가·삭제·순서 변경과 프레임 단위 타임라인 편집
