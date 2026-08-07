# Shortform Director AI 영상 제작 구현 계획

> 설계 기준: `architecture/2026-08-05-shortform-director-ai-video-production-design.md`
>
> 문서 상태: 구현 순서 확정
>
> 작업 브랜치: `feat/shortform-director-storyboard-only`

## 목표

현재의 주제 우선 흐름과 영상 후보 그리드는 유지한다. 선택한 영상 후보에서 다음 흐름을 완성한다.

1. 제작 모델과 제작 방식을 선택한다.
2. 선택한 모델의 컷 길이 제한을 반영해 스토리보드를 만든다.
3. Clipper 템플릿 방식이면 실제 TTS 길이로 스토리보드 타임라인을 다시 맞춘다.
4. Gemini Omni 또는 Seedance 2.0으로 각 컷의 720p 9:16 영상을 만든다.
5. 생성 영상을 로컬에 검증·저장한다.
6. 첫 번째 레거시 family의 full 템플릿으로 자막·TTS·효과음·선택 BGM을 합성한다.
7. 1080×1920 최종 MP4를 기존 Clipper 렌더 작업으로 만든다.

AI 통합 제작 방식은 공급자가 음성·자막·효과음을 포함한 영상을 만들고 Clipper 오버레이 없이 이어 붙여 렌더한다.

## 구현 원칙

- 공급자 API 키와 외부 API 호출은 `clipper_web_api`에서만 처리한다.
- 공급자 결과 MP4의 영구 저장은 `clipper_nestjs`의 `CLIPPER_DATA_DIR`에서만 처리한다.
- `clipper_web_api`는 공급자 작업 상태와 인증된 결과 스트림만 제공한다.
- 스토리보드 이후의 일반 렌더 기능은 새로 복제하지 않고 기존 `ShortformProjectService`와 `clipper_video_render` 작업을 재사용한다.
- 유료 공급자 호출은 자동 테스트에서 실행하지 않는다. 모든 공급자 테스트는 가짜 HTTP 응답과 로컬 fixture를 사용한다.
- 실패한 영상 컷 재생성은 새 비용 승인 없이는 새 공급자 요청을 만들지 않는다.
- 다운로드 재시도는 같은 공급자 결과를 다시 내려받으며 새 생성 요청을 만들지 않는다.

## 작업 1: 프로필 목표 길이를 15–60초 정수로 확장

### Desktop Nest 계약 및 저장

- 수정:
  - `desktop/clipper_nestjs/src/modules/shortform-director/domain/operating-profile.ts`
  - `desktop/clipper_nestjs/src/modules/shortform-director/domain/operating-profile.input.ts`
  - `desktop/clipper_nestjs/src/modules/shortform-director/presentation/dto/create-shortform-director-profile.dto.ts`
  - `desktop/clipper_nestjs/src/modules/shortform-director/presentation/dto/update-shortform-director-profile.dto.ts`
  - `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-candidate-generation.service.ts`
  - `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-candidate-production-preflight.service.ts`
  - `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-research-artifact.service.ts`
- 테스트:
  - `desktop/clipper_nestjs/test/shortform-director-profile-api.test.js`
  - `desktop/clipper_nestjs/test/shortform-director-profile-storage.test.js`

체크리스트:

- [ ] 먼저 16, 29, 31, 59가 허용되고 14, 61, 소수, 문자열이 거절되는 실패 테스트를 추가한다.
- [ ] `OperatingProfileDurationSec`를 숫자 타입으로 바꾸고 도메인 정규화와 DTO에 `IsInt`, `Min(15)`, `Max(60)`을 적용한다.
- [ ] 저장된 이전 15/30/45/60 값은 별도 마이그레이션 없이 그대로 읽히게 한다.
- [ ] 후보·조사 artifact 파서의 좁은 union 캐스트를 제거하고 동일한 범위 검사를 사용한다.

### Angular 프로필 폼

- 수정:
  - `desktop/clipper_angular/src/features/shortform-director/models/shortform-director-workspace.ts`
  - `desktop/clipper_angular/src/features/shortform-director/components/operating-profile-form/operating-profile-form.component.ts`
  - `desktop/clipper_angular/src/features/shortform-director/components/operating-profile-form/operating-profile-form.component.html`
  - `desktop/clipper_angular/src/features/shortform-director/components/operating-profile-form/operating-profile-form.component.scss`
  - `desktop/clipper_angular/src/features/shortform-director/components/operating-profile-form/operating-profile-form.component.spec.ts`

체크리스트:

- [ ] 먼저 생성 기본값 30과 수정 hydration, 15–60 범위 오류를 검증하는 컴포넌트 테스트를 추가한다.
- [ ] `type=number`, `min=15`, `max=60`, `step=1` 필드를 프로필 핵심 정보 영역에 추가한다.
- [ ] 값이 유효하지 않으면 저장 버튼을 비활성화하고 한국어 오류를 표시한다.

## 작업 2: 제작 선택과 스토리보드 계약

### 공통 제작 계약

- 추가:
  - `desktop/clipper_nestjs/src/modules/shortform-director/domain/ai-video-production.ts`
  - `desktop/clipper_nestjs/test/shortform-director-ai-video-production-contract.test.js`
- 수정:
  - `desktop/clipper_nestjs/src/modules/shortform-director/domain/shortform-director.model.ts`
  - `desktop/clipper_nestjs/src/modules/shortform-director/domain/production-state.ts`
  - `desktop/clipper_nestjs/src/modules/shortform-director/infrastructure/json-shortform-director-project.repository.ts`

계약:

```ts
type AiVideoModel = 'gemini-omni' | 'seedance-2.0';
type AiVideoProductionMode = 'clipper-template' | 'ai-integrated';

interface AiVideoProductionConfigV1 {
  schemaVersion: 'ai-video-production-config.v1';
  model: AiVideoModel;
  mode: AiVideoProductionMode;
}
```

체크리스트:

- [ ] 먼저 모델별 컷 길이와 비용률, 720×1280 출력 규칙을 검증하는 도메인 테스트를 작성한다.
- [ ] Gemini Omni는 3–10초, Seedance 2.0은 4–15초로 고정한다.
- [ ] 프로젝트 production state에 선택 snapshot과 제작 revision lock을 저장한다.
- [ ] 선택이 없는 과거 프로젝트는 읽을 수 있지만 새 스토리보드 생성에는 선택이 필요하게 한다.

### 스토리보드 입력과 컷 분할

- 수정:
  - `desktop/clipper_nestjs/src/modules/shortform-director/presentation/dto/start-shortform-director-candidate-production.dto.ts`
  - `desktop/clipper_nestjs/src/modules/shortform-director/presentation/shortform-director-candidate-production.controller.ts`
  - `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-candidate-production-preflight.service.ts`
  - `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-candidate-production.service.ts`
  - `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-candidate-plan.compiler.ts`
  - `desktop/clipper_nestjs/test/shortform-director-candidate-production.test.js`
  - `desktop/clipper_nestjs/test/shortform-director-candidate-plan-compiler.test.js`
  - `web/clipper_web_api/src/modules/shortform-director-inference/application/shortform-director-inference.prompt.ts`
  - `web/clipper_web_api/src/modules/shortform-director-inference/application/shortform-director-inference.prompt.spec.ts`

체크리스트:

- [ ] 먼저 제작 선택이 승인 snapshot과 요청 body에 포함되는 실패 테스트를 추가한다.
- [ ] 스토리보드 프롬프트에 모델별 최소·최대 컷 길이, 9:16 720p, 제작 방식별 오디오·텍스트 제약을 넣는다.
- [ ] 컴파일러가 모든 시각 컷을 선택 모델 제한 안으로 분할하고 전체 장면 시간을 빈틈없이 보존하는 테스트를 추가한다.
- [ ] Clipper 방식 프롬프트는 화면 내 글자·나레이션·대화·BGM을 금지하고 ambient/SFX만 요청하게 한다.
- [ ] AI 통합 방식 프롬프트는 장면별 말할 내용과 화면 자막을 생성 영상 프롬프트에 포함하게 한다.

### Angular 제작 선택 UI

- 추가:
  - `desktop/clipper_angular/src/features/shortform-director/components/production-setup-card/production-setup-card.component.ts`
  - `desktop/clipper_angular/src/features/shortform-director/components/production-setup-card/production-setup-card.component.html`
  - `desktop/clipper_angular/src/features/shortform-director/components/production-setup-card/production-setup-card.component.scss`
  - `desktop/clipper_angular/src/features/shortform-director/components/production-setup-card/production-setup-card.component.spec.ts`
- 수정:
  - `desktop/clipper_angular/src/features/shortform-director/models/shortform-director-production.ts`
  - `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-production.gateway.ts`
  - `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-production.service.ts`
  - `desktop/clipper_angular/src/features/shortform-director/state/shortform-director-production.store.ts`
  - `desktop/clipper_angular/src/features/shortform-director/pages/production-page/production-page.component.ts`
  - `desktop/clipper_angular/src/features/shortform-director/pages/production-page/production-page.component.html`

체크리스트:

- [ ] 먼저 모델명 `Gemini Omni`, `Seedance 2.0`과 제작 방식 두 개가 표시되는 컴포넌트 테스트를 추가한다.
- [ ] 기본값은 `Gemini Omni`와 `Clipper 템플릿 방식`으로 한다.
- [ ] 모델 카드에 컷 최대 길이와 720p 9:16을 표시한다.
- [ ] 기존 스토리보드가 있으면 선택을 읽기 전용으로 표시하고 변경 시 새 스토리보드 revision을 만들도록 안내한다.

## 작업 3: FAL credential 관리

### Web API

- 추가:
  - `web/clipper_web_api/src/modules/provider-credentials/application/fal-credential.service.ts`
  - `web/clipper_web_api/src/modules/provider-credentials/application/fal-credential.service.spec.ts`
- 수정:
  - `web/clipper_web_api/src/modules/provider-credentials/domain/provider-credential.model.ts`
  - `web/clipper_web_api/src/modules/provider-credentials/provider-credentials.module.ts`
  - `web/clipper_web_api/src/modules/api-keys/application/api-keys.service.ts`
  - `web/clipper_web_api/src/modules/api-keys/application/api-keys.service.spec.ts`
  - `web/clipper_web_api/src/modules/api-keys/presentation/dto/create-api-key.dto.ts`
  - `web/clipper_web_api/src/modules/api-keys/presentation/api-keys.controller.ts`
  - `web/clipper_web_api/src/modules/api-keys/presentation/api-keys.controller.spec.ts`
  - `web/clipper_web_api/src/modules/api-keys/presentation/api-keys.openapi.spec.ts`
  - Web API OpenAPI source와 생성 산출물

체크리스트:

- [ ] 먼저 `fal` 생성·활성화·마스킹·runtime status·credential test 테스트를 추가한다.
- [ ] provider union에 `fal`을 추가하고 기존 다중 credential 활성화 규칙을 재사용한다.
- [ ] test는 FAL queue endpoint에 인증된 최소 검증 요청을 보내지 않고, 인증 가능한 read endpoint를 사용한다.
- [ ] OpenAPI 계약을 먼저 수정하고 controller 응답을 일치시킨다.

### Web Admin

- 작업 시작 전 `feat/shortform-director-foundation`에서 `feat/shortform-director-storyboard-only` 브랜치를 만든다.
- 수정:
  - `web/clipper_web_admin/src/app/features/portal/api-keys/api-keys.types.ts`
  - `web/clipper_web_admin/src/app/features/portal/api-keys/api-keys.view-model.ts`
  - `web/clipper_web_admin/src/app/features/portal/api-keys/services/manual-provider-credential.facade.ts`
  - `web/clipper_web_admin/src/app/features/portal/api-keys/api-keys.component.ts`
  - `web/clipper_web_admin/src/app/features/portal/api-keys/api-keys.component.html`
  - `web/clipper_web_admin/src/app/features/portal/api-keys/api-keys.component.spec.ts`
  - `web/clipper_web_admin/src/app/core/api/api-keys-api.service.ts`

체크리스트:

- [ ] 먼저 FAL 섹션과 추가·수정 payload를 검증하는 컴포넌트 테스트를 추가한다.
- [ ] Gemini/YouTube에 쓰는 수동 credential UI를 FAL에도 재사용한다.
- [ ] 화면에는 raw secret을 절대 다시 표시하지 않는다.

## 작업 4: first-family full 시스템 템플릿

- 추가:
  - `desktop/clipper_nestjs/src/modules/template-builder/domain/template-builder-full-family.ts`
  - `desktop/clipper_nestjs/src/modules/template-builder/assets/fonts/Pretendard-Bold.otf`
  - `desktop/clipper_nestjs/src/modules/template-builder/assets/fonts/JalnanGothic.otf`
  - `desktop/clipper_nestjs/src/modules/projects/assets/clipper-studio-seed/template/layout_legacy_1_full.png`
  - `desktop/clipper_nestjs/src/modules/projects/assets/legacy-clipper1-template-ui/thumbs-and-origins/1_ratio_full_thumb.png`
  - `desktop/clipper_nestjs/src/modules/projects/assets/legacy-clipper1-template-ui/thumbs-and-origins/1_ratio_full_origin.png`
  - 로컬 gradient PNG
  - `desktop/clipper_nestjs/test/template-builder-full-family.test.js`
- 수정:
  - `desktop/clipper_nestjs/src/modules/template-builder/domain/template-builder.model.ts`
  - `desktop/clipper_nestjs/src/modules/template-builder/domain/shortform-template-runtime-spec.ts`
  - `desktop/clipper_nestjs/src/modules/template-builder/application/template-builder.service.ts`
  - `desktop/clipper_nestjs/src/modules/project-manifest/infrastructure/template-builder-published-preset-source.ts`
  - `desktop/clipper_nestjs/src/modules/project-manifest/infrastructure/template-builder-template-asset.service.ts`
  - 빌드 asset 복사 설정

체크리스트:

- [ ] 먼저 `archive/template-builder-full-2026-06-12`의 catalog id 4 값과 완전히 일치하는 시스템 family snapshot 테스트를 추가한다.
- [ ] `full`은 내부 시스템 variant 타입에는 허용하되 사용자 생성 DTO와 UI의 1:1/4:3 선택지는 늘리지 않는다.
- [ ] content area는 1080×1920 전체 화면이며 runtime frame은 확대·크롭 없이 1080×1920이다.
- [ ] 레거시 S3 URI를 로컬 asset URI로 치환한다.
- [ ] 시스템 family는 읽기 전용이고 full variant 하나만 가진다.
- [ ] published preset source와 Director 렌더 어댑터가 이 preset id를 사용한다.

## 작업 5: 공급자 영상 작업 API

- 추가:
  - `web/clipper_web_api/src/modules/shortform-director-video-generation/domain/shortform-director-video-job.ts`
  - `web/clipper_web_api/src/modules/shortform-director-video-generation/application/shortform-director-video-job.service.ts`
  - `web/clipper_web_api/src/modules/shortform-director-video-generation/infrastructure/gemini-omni-video.adapter.ts`
  - `web/clipper_web_api/src/modules/shortform-director-video-generation/infrastructure/seedance-video.adapter.ts`
  - `web/clipper_web_api/src/modules/shortform-director-video-generation/infrastructure/in-memory-shortform-director-video-job.repository.ts`
  - `web/clipper_web_api/src/modules/shortform-director-video-generation/presentation/shortform-director-video-job.controller.ts`
  - DTO, module, adapter/service/controller spec 파일
- 수정:
  - `web/clipper_web_api/src/modules/shortform-director-production/domain/shortform-director-production-capability-catalog.ts`
  - `web/clipper_web_api/src/app.module.ts`
  - Web API OpenAPI source와 생성 산출물

HTTP 계약:

```text
GET  /shortform-director/video-models
POST /shortform-director/video-jobs
GET  /shortform-director/video-jobs/:jobId
GET  /shortform-director/video-jobs/:jobId/result
```

체크리스트:

- [ ] 먼저 capability catalog가 Gemini Omni와 Seedance 2.0만 노출하고 가격·길이·해상도를 고정하는 테스트를 작성한다.
- [ ] create 요청은 idempotency key, model, mode, duration, 9:16 prompt, project/shot/revision lineage를 받는다.
- [ ] 서비스는 같은 idempotency key에 새 공급자 요청을 만들지 않는다.
- [ ] Gemini adapter는 Interactions 생성 후 Google file이 `ACTIVE`가 될 때까지 상태를 조회하고 인증된 download URI를 반환한다.
- [ ] Seedance adapter는 queue submit/status/result를 사용하고 `X-Fal-Retry: 0`, `resolution=720p`, `aspect_ratio=9:16`, `generate_audio=true`를 보낸다.
- [ ] Web API는 공급자 결과를 버퍼링하거나 영구 저장하지 않고 인증된 스트림으로 전달한다.
- [ ] 결과 endpoint는 아직 준비되지 않았으면 409, 실패면 안정적인 오류 코드, 준비되면 video stream을 반환한다.
- [ ] 작업 metadata는 첫 구현에서 프로세스 메모리에 유지하며 Desktop의 idempotency/lineage로 중복 과금을 막는다. 서버 재시작 뒤 공급자 request id 복구가 필요해지면 별도 DB migration으로 확장한다.

## 작업 6: Desktop 영상 작업, 다운로드, 로컬 저장

- 추가:
  - `desktop/clipper_nestjs/src/modules/shortform-director/domain/ai-video-job.ts`
  - `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-ai-video-web-api.client.ts`
  - `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-ai-video.service.ts`
  - `desktop/clipper_nestjs/src/modules/shortform-director/infrastructure/local-shortform-director-generated-video.storage.ts`
  - `desktop/clipper_nestjs/src/modules/shortform-director/presentation/shortform-director-ai-video.controller.ts`
  - DTO와 대응 `node:test` 파일
- 수정:
  - `desktop/clipper_nestjs/src/modules/shortform-director/domain/production-state.ts`
  - `desktop/clipper_nestjs/src/modules/shortform-director/shortform-director.module.ts`

체크리스트:

- [ ] 먼저 작업 상태 전이와 같은 revision 재호출의 idempotency 테스트를 작성한다.
- [ ] 저장 경로를 `shortform-director/projects/<projectId>/assets/generated/<shotId>/<revisionId>.mp4`로 고정한다.
- [ ] `.part`에 스트리밍하며 256MB 상한, `video/mp4`, MP4 container, 720×1280, 계획 길이 이상, 오디오 stream, SHA-256을 검사한다.
- [ ] 검증 성공 후 atomic rename하고 실패 시 `.part`를 제거한다.
- [ ] 다운로드 실패는 같은 Web API job의 result endpoint만 재시도한다.
- [ ] 상태를 `planned → queued → generating → output_ready → downloading → ready`와 세분화된 실패로 저장한다.

## 작업 7: Clipper TTS 기준 타임라인

- 추가 또는 선별 복원:
  - `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-narration.service.ts`
  - `desktop/clipper_nestjs/src/modules/shortform-director/presentation/shortform-director-narration.controller.ts`
  - 필요한 narration storage/domain 파일
- 재사용:
  - `desktop/clipper_nestjs/src/modules/shortform/application/tts/shortform-tts.service.ts`
  - `desktop/clipper_nestjs/src/modules/shortform-director/domain/video-plan-timing-alignment.ts`
- 테스트:
  - narration 합성, timing alignment, revision lock 테스트

체크리스트:

- [ ] 먼저 실제 TTS 측정값 34.7초가 30초 목표 스토리보드를 34.7초로 확장하는 테스트를 추가한다.
- [ ] 기존 숏폼 TTS preset과 합성 provider를 재사용한다.
- [ ] cue별 WAV와 실제 duration을 저장하고 `alignVideoPlanTiming`으로 scene/beat/shot/layer 시간을 다시 계산한다.
- [ ] 모델별 컷 최대 길이를 넘은 장면은 TTS 타임라인 안에서 여러 생성 컷으로 다시 분할한다.
- [ ] Seedance 정수 duration 요청은 계획보다 짧지 않은 지원 값을 선택하고 최종 렌더에서 visual/SFX tail만 자른다.
- [ ] 첫 공급자 작업 제출 뒤 speaker/speed/timeline을 lock한다.

## 작업 8: Director → 기존 Clipper 렌더 어댑터

- 추가:
  - `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-clipper-render.adapter.ts`
  - `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-final-render.service.ts`
  - `desktop/clipper_nestjs/src/modules/shortform-director/presentation/shortform-director-final-render.controller.ts`
  - DTO와 대응 테스트
- 수정:
  - `desktop/clipper_nestjs/src/modules/shortform/shortform.module.ts`
  - `desktop/clipper_nestjs/src/modules/shortform/application/shortform-project.service.ts`
  - `desktop/clipper_nestjs/src/modules/shortform-core/domain/shortform-core.model.ts`
  - `desktop/clipper_nestjs/src/modules/shortform-director/shortform-director.module.ts`

체크리스트:

- [ ] 먼저 Director shot·narration·caption이 기존 `ShortformProject` clip·media slot·TTS artifact로 정확히 변환되는 테스트를 추가한다.
- [ ] 일반 `ShortformProjectService`에 내부용 `createPreparedProject` 경계를 추가해 이미 준비된 clip/asset/TTS를 저장하게 한다.
- [ ] full 시스템 template preset, 1080×1920 output, 선택 BGM을 render settings에 넣는다.
- [ ] Clipper 방식은 TTS 1.0, AI 원본 오디오 낮춤, BGM 최저 볼륨과 ducking으로 섞는다.
- [ ] AI 통합 방식은 공급자 혼합 음성을 유지하고 Clipper TTS·caption layer·BGM을 추가하지 않는다.
- [ ] 생성 영상이 계획보다 길면 visual/SFX tail만 컷 경계에서 trim하고, 짧으면 렌더를 막는다.
- [ ] 최종 결과를 `shortform-director/projects/<projectId>/renders/<renderId>.mp4`에서 조회할 수 있게 연결한다.

## 작업 9: 제작 실행 및 상태 UI

- 추가:
  - `desktop/clipper_angular/src/features/shortform-director/components/ai-video-production-card/ai-video-production-card.component.ts`
  - 대응 HTML/SCSS/spec
  - `desktop/clipper_angular/src/features/shortform-director/components/ai-video-shot-status-list/ai-video-shot-status-list.component.ts`
  - 대응 HTML/SCSS/spec
- 수정:
  - production model/gateway/service/store/page 4-file 세트
  - `desktop/clipper_angular/src/features/shortform-director/components/storyboard-scene-list/*`

체크리스트:

- [ ] 먼저 Clipper 방식의 TTS/BGM 선택과 AI 통합 방식의 옵션 숨김을 검증한다.
- [ ] 스토리보드 아래에 TTS 생성, 영상 비용 승인, 컷별 상태, 실패 컷 재승인, 최종 렌더 순서만 표시한다.
- [ ] 내부 job id와 credential id는 기본 화면에서 숨기고 “근거와 과정” disclosure 안에서만 보여준다.
- [ ] 페이지 재진입 시 저장된 production state를 읽어 진행 중/완료 작업을 복구한다.
- [ ] 최종 MP4가 준비되면 재생과 파일 열기 동작을 제공한다.

## 작업 10: 검증

체크리스트:

- [ ] 각 작업은 실패 테스트를 먼저 실행해 의도한 이유로 실패하는 것을 확인한다.
- [ ] 각 작업의 최소 구현 후 해당 테스트만 통과시킨다.
- [ ] Web API `npm run build`, `npm test -- --runInBand`.
- [ ] Web Admin `npm run build`, `npm test -- --watch=false --browsers=ChromeHeadless`.
- [ ] Desktop Nest `npm run build`, 변경된 `node --test` 묶음.
- [ ] Angular `npm run build`, `npm test -- --watch=false --browsers=ChromeHeadless`.
- [ ] 네 저장소 `git diff --check`.
- [ ] 로컬 mock 공급자로 앱을 실행해 모델/방식 선택 → 스토리보드 → TTS alignment → 가짜 MP4 저장 → 기존 렌더 job 연결을 smoke test한다.
- [ ] Gemini/FAL 실제 유료 생성 호출은 별도 사용자 승인 전에는 실행하지 않는다.
- [ ] 구현 완료 전 설계 문서의 수용 기준을 한 항목씩 대조해 누락을 기록한다.

## 구현 순서와 커밋 경계

1. 프로필 목표 길이
2. 제작 선택과 스토리보드 컷 제한
3. FAL credential
4. full 시스템 템플릿
5. Web API 공급자 작업
6. Desktop 다운로드·저장
7. TTS 타임라인
8. 기존 Clipper 렌더 어댑터
9. 제작 UI와 복구
10. 전체 검증

문서는 사용자의 지시에 따라 코드 변경 커밋에 포함하지 않는다. 코드 커밋과 push는 별도 지시를 따르며, 실제 공급자 유료 호출 역시 별도 승인 없이는 수행하지 않는다.
