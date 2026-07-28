# AI 숏폼 디렉터 — YouTube 레퍼런스 영상 정밀 분석 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:subagent-driven-development` (recommended) or
> `superpowers:executing-plans` to implement this plan task-by-task. Use
> `superpowers:test-driven-development` for every behavior change and
> `superpowers:verification-before-completion` before reporting completion.

**Goal:** AI 디렉터 조사가 YouTube 검색 후보를 최대 6개까지 실제로 수집하고 추천
3개를 사용자가 교체할 수 있게 한 뒤, 별도 비용 승인 후 선택한 공개 YouTube 영상
3개를 실제 영상·자막·컷·주요 프레임 기준으로 정밀 분석해 검증된 레퍼런스 패턴과
최신 조사 주제를 생성하게 한다.

**Architecture:** 데스크톱 Nest가 조사 실행, 후보·선택·미디어 전처리, 로컬 JSON 계보와
검증을 소유한다. 초기 시장 조사인 부모 `research` run은 후보를 게시한 뒤
`awaiting_reference_selection`으로 안전하게 멈춘다. 정밀 분석은 별도
`reference-analysis` 자식 run에서 비동기로 수행해 영상 하나의 실패나 앱 재시작이
부모 조사를 없애지 않게 한다. API key는 기존 관리자 DB에만 남고, 인증된 Web API가
Gemini Interactions 영상 분석을 대신 수행한다. 자막이 없는 영상은 대사 하이라이트
플러그인의 기존 로컬 `faster-whisper-small` STT를 공통 플러그인 실행 경계 아래에서
재사용한다. Angular는 후보 교체, 두 번째 비용 승인, 영상별 진행 상태, 분석 결과와
근거를 기존 아이디어 찾기 서브페이지 안에서 보여준다.

**Tech Stack:** Angular 19 standalone/zoneless + Angular Material · NestJS 11
(desktop/web API) · Python local plugin host · faster-whisper · local JSON/files · yt-dlp ·
FFmpeg/ffprobe · YouTube Data API v3 · Gemini Interactions API · OpenAI Responses API ·
node:test · pytest · Jest · Karma/Jasmine.

**Approved design:**

`.codex/design/SHORTFORM_DIRECTOR_REFERENCE_VIDEO_DEEP_ANALYSIS_DESIGN_2026-07-29.md`

---

## 0. 구현 시작 기준점

계획 작성 시점인 2026-07-29 KST의 기준점은 다음과 같다.

| 저장소 | branch / HEAD | upstream | 작업 트리 |
|---|---|---:|---:|
| `desktop/clipper_nestjs` | `feat/shortform-director-foundation` / `975a298` | `0/0` | 92개 변경 |
| `desktop/clipper_angular` | `feat/shortform-director-foundation` / `a70bc39` | `0/0` | 47개 변경 |
| `desktop/clipper_python` | `dev` / `6688885` | `0/0` | clean |
| `web/clipper_web_api` | `feat/shortform-director-foundation` / `c468ec0` | `0/0` | 12개 변경 |
| `.codex` | `main` / `285cb6e` | `0/0` | 이 계획을 포함해 4개 미추적 설계 문서 |

현재 변경에는 이미 진행 중인 제작 모델·장면 수정 기능과 실제 조사 장애 진단 변경이
섞여 있다. 구현자는 다음을 지킨다.

- reset, revert, checkout으로 기존 변경을 없애지 않는다.
- 별도 worktree를 만들지 않는다.
- 같은 파일을 수정하기 전에 현재 diff를 읽고 기존 의도를 보존한다.
- `legacy/adlight_python/fastapi_server.spec`는 열람·stage·format·commit 대상이 아니다.
- 이 계획 파일과 구현 변경은 사용자가 명시적으로 요청하기 전에는 commit/push하지 않는다.
- 체크포인트의 commit 명령은 사용자가 commit을 요청한 경우에만 실행한다.

각 Task 시작 전 아래 명령으로 기준점 이탈을 확인한다.

```bash
git -C desktop/clipper_nestjs status --short --branch
git -C desktop/clipper_angular status --short --branch
git -C desktop/clipper_python status --short --branch
git -C web/clipper_web_api status --short --branch
git -C .codex status --short --branch
```

예상하지 못한 새 변경이 있으면 겹치는 파일을 수정하지 말고 사용자에게 먼저 보고한다.

---

## 1. 전역 제약

- **실제 실행만 성공 처리:** 런타임에서 fixture, 가짜 provider 응답, 빈 성공 결과,
  metadata-only Gemini 대체 결과를 사용하지 않는다.
- **두 번의 비용 승인:** 첫 승인은 가벼운 시장·후보 조사만 승인한다. 두 번째 승인은
  정확히 선택된 영상, 실제 길이, 모델, 기본 호출 수, 최대 재시도 수, 예상 비용을
  고정한다.
- **credential 경계:** Electron 환경 파일이나 로컬 JSON에 API key를 넣지 않는다.
  Web API는 기존 관리자 페이지에서 등록된 credential ID/revision을 확인하고 DB의
  원문 key를 사용한다.
- **크레딧 제외:** AI Director research/reference-analysis에서 operation quote,
  credit authorize/charge/refund/ledger를 호출하지 않는다.
- **로컬 JSON SoT:** source call, 후보 점수, 선택 revision, 승인 snapshot, 전처리
  manifest, 실제 전송한 텍스트 prompt, 파싱 결과, validation, usage, 비용을 immutable
  JSON artifact로 저장한다.
- **provider raw 미저장:** provider 원문 response body와 원문 오류 body는 JSON
  artifact에 저장하지 않는다. 필요한 공개 필드만 즉시 파싱한다.
- **binary 분리:** MP4/WAV/JPEG bytes와 base64는 JSON에 넣지 않는다. JSON에는
  media ID, 상대 경로, MIME, byte size, SHA-256, timestamp만 둔다.
- **한 영상 한 호출:** Gemini 요청 하나에는 공개 YouTube 영상 하나만 넣는다.
- **Google 공식 계약:** `POST /v1beta/interactions`, video URI, 마지막 text prompt,
  `response_format = { type: "text", mime_type: "application/json", schema }`를 쓴다.
- **빠른 컷 보완:** Gemini 기본 1 FPS 영상 처리에만 의존하지 않고 FFmpeg가 전체
  영상을 디코딩해 컷을 계산하고 최대 12개 대표 JPEG를 추가 입력한다.
- **검증 우선:** duration, 컷 수, 첫 3초 컷 수, shot 길이는 로컬 계산값만 게시한다.
  Gemini가 반환한 timestamp와 evidence ref는 로컬 validator를 통과해야 한다.
- **저작권 경계:** 레퍼런스 영상과 프레임은 형식 분석 근거다. 제작용 asset으로 자동
  승격하지 않는다.
- **기존 뒤 파이프라인 유지:** 검증된 topic 이후에는 기존 topic별 영상 후보 10개 이상,
  장면 제작, Motion Canvas 렌더, Jobs/Projects 보관함 흐름을 그대로 사용한다.
- **no Remotion:** 코드, UI, 문서, 오류 메시지에 대체 렌더러로도 추가하지 않는다.

### 1.1 기존 로컬 STT 재사용 계약

자막 fallback을 위해 새 OpenAI 전사 API를 추가하지 않는다. 대사 하이라이트에 이미
구현된 `faster-whisper-small`과 `stt_worker.py::run_stt`를 단일 구현으로 재사용한다.

- 제작자/자동 VTT 자막: 각 cue에 실제 `startMs`, `endMs`를 저장한다.
- STT fallback: 기존 출력의 segment와 word별 실제 `start`, `end`를 밀리초 transcript
  계약으로 정규화한다.
- 별도 STT 모델 다운로드, Web API endpoint, OpenAI credential·비용 항목을 만들지 않는다.
- AI Director는 `DialogHighlightWorkflowExecutor`를 호출하지 않으므로 대사 하이라이트의
  operation quote나 크레딧 차감을 통과하지 않는다.
- 기존 `analyze_media` 전체는 OpenCLIP·audio embedding 등 불필요한 작업까지 포함하므로
  호출하지 않는다. 같은 `run_stt`를 쓰는 좁은 `transcribe_media` local stage를 추가한다.
- spoken hook 직접 문구는 timestamp가 있는 transcript에 실제 포함될 때만 게시한다.
- 구조 timestamp는 Gemini 영상 관찰과 로컬 frame/cut evidence로 검증한다.

---

## 2. 파일 및 책임 지도

### 2.1 `desktop/clipper_nestjs`

**기존 파일 수정**

- `src/core/web-api/web-api-client.service.ts`
  - Gemini frame 전송을 위한 인증된 multipart POST 지원
- `src/modules/dialog-highlight/application/dialog-highlight-python-stage.runner.ts`
  - 기존 대사 하이라이트 workflow가 공통 local plugin runner를 사용하도록 위임
- `src/modules/sources/application/source.service.ts`
  - 기존 yt-dlp 인증·캐시를 재사용한 레퍼런스 영상/자막 획득
- `src/modules/sources/domain/source.model.ts`
  - 레퍼런스 획득 결과 계약
- `src/modules/shortform-director/domain/run-record.ts`
  - `awaiting_reference_selection`, `reference-analysis` run kind
- `src/modules/shortform-director/domain/shortform-director-run.repository.ts`
  - active 상태 전환 계약
- `src/modules/shortform-director/infrastructure/local-shortform-director-run.repository.ts`
  - active 상태의 ref attach와 원자적 상태 전환
- `src/modules/shortform-director/infrastructure/shortform-director-run-index.ts`
  - project 없는 reference-analysis run 위치
- `src/modules/shortform-director/application/shortform-director-lineage-publisher.service.ts`
  - terminal status 타입 명확화
- `src/modules/shortform-director/application/shortform-director-lineage-publisher-input.snapshot.ts`
  - terminal status 타입 명확화
- `src/modules/shortform-director/domain/research-cost-estimate.ts`
  - 첫 조사 승인 범위를 discovery로 축소
- `src/modules/shortform-director/application/shortform-director-research-preflight.service.ts`
  - 첫 승인에서 Gemini 제외
- `src/modules/shortform-director/application/shortform-director-research-source.collector.ts`
  - Naver와 YouTube 후보 탐색/선택 댓글 수집 분리
- `src/modules/shortform-director/application/shortform-director-research-input.builder.ts`
  - metadata-only 분석 입력 제거
- `src/modules/shortform-director/application/shortform-director-research-artifact.service.ts`
  - 후보·선택·분석·패턴 typed reader
- `src/modules/shortform-director/application/shortform-director-research.service.ts`
  - facade 역할로 축소
- `src/modules/shortform-director/application/shortform-director-research-topic.builder.ts`
  - 검증된 reference patterns 입력
- `src/modules/shortform-director/application/shortform-director-research.models.ts`
  - 공개 후보·선택·preflight·attempt 계약
- `src/modules/shortform-director/presentation/shortform-director-research.controller.ts`
  - 후보·선택·비용·분석·미디어 endpoint
- `src/modules/shortform-director/shortform-director.module.ts`
  - `SourcesModule` 및 새 서비스 등록

**새 파일**

- `src/modules/shortform-director/domain/reference-candidate.ts`
- `src/modules/shortform-director/domain/reference-analysis.ts`
- `src/modules/shortform-director/domain/reference-analysis-cost-estimate.ts`
- `src/modules/shortform-director/application/shortform-director-reference-candidate.collector.ts`
- `src/modules/shortform-director/application/shortform-director-reference-candidate.ranker.ts`
- `src/modules/shortform-director/application/shortform-director-reference-selection.service.ts`
- `src/modules/shortform-director/application/shortform-director-reference-analysis-preflight.service.ts`
- `src/modules/shortform-director/application/shortform-director-reference-media.preprocessor.ts`
- `src/modules/shortform-director/application/shortform-director-reference-local-stt.client.ts`
- `src/modules/shortform-director/application/shortform-director-reference-analysis.validator.ts`
- `src/modules/shortform-director/application/shortform-director-reference-analysis-web-api.client.ts`
- `src/modules/shortform-director/application/shortform-director-reference-analysis.orchestrator.ts`
- `src/modules/shortform-director/application/shortform-director-reference-analysis.runner.ts`
- `src/modules/shortform-director/application/shortform-director-research-discovery.service.ts`
- `src/modules/shortform-director/infrastructure/local-shortform-director-reference-media.storage.ts`
- `src/modules/shortform-director/infrastructure/shortform-director-reference-media-tool.runner.ts`
- `src/modules/plugins/application/local-plugin-job.runner.ts`
- `src/modules/shortform-director/presentation/dto/update-shortform-director-reference-selection.dto.ts`
- `src/modules/shortform-director/presentation/dto/start-shortform-director-reference-analysis.dto.ts`

**테스트**

- `test/shortform-director-run-storage.test.js`
- `test/shortform-director-research-cost-estimate.test.js`
- `test/shortform-director-reference-candidates.test.js`
- `test/shortform-director-reference-selection.test.js`
- `test/shortform-director-reference-analysis-cost.test.js`
- `test/shortform-director-reference-media.test.js`
- `test/shortform-director-reference-local-stt.test.js`
- `test/shortform-director-reference-analysis-client.test.js`
- `test/shortform-director-reference-analysis-validation.test.js`
- `test/shortform-director-reference-analysis-orchestrator.test.js`
- `test/shortform-director-research-orchestrator.test.js`
- `test/web-api-client.test.js`

### 2.2 `desktop/clipper_python`

**기존 파일 수정**

- `plugins/dialog_highlight/dialog_highlight/services/stage_contracts.py`
  - `transcribe_media` stage 계약 추가
- `plugins/dialog_highlight/dialog_highlight/services/stage_runner.py`
  - 기존 `stt_worker.run_stt`만 호출하는 좁은 stage 추가

`stt_worker.py`의 Whisper 구현은 복제하거나 교체하지 않는다.

**테스트**

- `tests/test_dialog_transcribe_stage.py`
- `tests/test_dialog_stage_contracts.py`

### 2.3 `web/clipper_web_api`

**기존 파일 수정**

- `docs/api/openapi.yaml`
  - 영상 분석 multipart 계약
- `src/app.module.ts`
  - 새 module import
- `src/modules/shortform-director-research/application/youtube-data-provider.service.ts`
  - `videos.list`에 공개 상태 확인용 `status` part
- `src/modules/shortform-director-inference/domain/shortform-director-inference.contract.ts`
- `src/modules/shortform-director-inference/domain/shortform-director-model-catalog.ts`
- `src/modules/shortform-director-inference/application/shortform-director-inference.prompt.ts`
  - 실패한 metadata-only `youtube-reference-analysis` 제거,
    `reference-pattern-synthesis` 추가

**새 module**

- `src/modules/shortform-director-reference-analysis/domain/reference-analysis.contract.ts`
- `src/modules/shortform-director-reference-analysis/domain/reference-analysis.transport.ts`
- `src/modules/shortform-director-reference-analysis/application/reference-analysis.prompt.ts`
- `src/modules/shortform-director-reference-analysis/application/shortform-director-reference-analysis.service.ts`
- `src/modules/shortform-director-reference-analysis/infrastructure/google-reference-video-analysis.transport.ts`
- `src/modules/shortform-director-reference-analysis/presentation/dto/reference-analysis-multipart.parser.ts`
- `src/modules/shortform-director-reference-analysis/presentation/shortform-director-reference-analysis.controller.ts`
- `src/modules/shortform-director-reference-analysis/shortform-director-reference-analysis.module.ts`

각 구현 파일에는 같은 이름의 `.spec.ts`를 둔다. controller 계약과 OpenAPI 일치는
`shortform-director-reference-analysis.openapi.spec.ts`에서 검증한다.

### 2.4 `desktop/clipper_angular`

**기존 파일 수정**

- `src/features/shortform-director/models/shortform-director-research.ts`
- `src/features/shortform-director/services/shortform-director-research.gateway.ts`
- `src/features/shortform-director/services/shortform-director-research.service.ts`
- `src/features/shortform-director/state/shortform-director-research.store.ts`
- `src/features/shortform-director/pages/ideas-page/ideas-page.component.{ts,html,scss,spec.ts}`
- `src/features/shortform-director/components/research-run-list/*`
- `src/core/errors/error-catalog.ts`
- `src/core/errors/error-catalog.spec.ts`

**새 standalone components**

- `components/research-reference-candidate-list/*`
- `components/research-reference-analysis-preflight/*`
- `components/research-reference-analysis-progress/*`
- `components/research-reference-analysis-detail/*`

페이지는 조율만 하고 후보 선택, 비용 표시, 진행 상태, 상세 분석 렌더링을 각각의
컴포넌트에 분리한다.

---

## Task 1. 중간 대기 상태와 자식 분석 run을 저장소 계약에 추가

**Files**

- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/domain/run-record.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/domain/shortform-director-run.repository.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/infrastructure/local-shortform-director-run.repository.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/infrastructure/shortform-director-run-index.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-lineage-publisher.service.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-lineage-publisher-input.snapshot.ts`
- Test: `desktop/clipper_nestjs/test/shortform-director-run-storage.test.js`

- [ ] **Step 1: 실패하는 상태 저장 테스트 작성**

다음을 검증한다.

- `research` run을 `running → awaiting_reference_selection → running`으로 전환한다.
- awaiting run에는 `finishedAt`이 없고 artifact ref를 추가할 수 있다.
- `reference-analysis` run은 `projectId` 없이 생성할 수 있다.
- recovery 목록은 실제 `running`만 포함하고 awaiting parent는 포함하지 않는다.
- terminal run에는 active 전환과 ref 추가가 실패한다.

- [ ] **Step 2: RED 확인**

```bash
cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/shortform-director-run-storage.test.js
```

예상: 새 status/kind/parser/repository method가 없어 실패한다.

- [ ] **Step 3: active/terminal 타입과 원자적 전환 구현**

`run-record.ts`에 다음 타입을 추가한다.

```ts
export type LocalRunActiveStatus =
  | 'running'
  | 'awaiting_reference_selection';

export type LocalRunTerminalStatus =
  | 'partial'
  | 'succeeded'
  | 'failed'
  | 'cancelled';

export type LocalRunStatus =
  | LocalRunActiveStatus
  | LocalRunTerminalStatus;
```

`LocalRunKind`에는 `reference-analysis`를 추가한다. parser는 active status에는
`finishedAt`을 금지하고 terminal status에는 요구한다.

repository에는 다음 계약을 추가한다.

```ts
abstract transitionActive(
  ownerSubjectId: string,
  runId: string,
  expected: LocalRunActiveStatus,
  next: LocalRunActiveStatus,
  patch?: LocalRunReferencePatch,
): Promise<LocalRunManifestV1 | null>;
```

`updateRefs()`는 active status에서만 허용한다. 기존 `transitionRunning()`은
`LocalRunTerminalStatus`만 받고 다른 제작 run의 의미는 바꾸지 않는다.

- [ ] **Step 4: GREEN 및 회귀 확인**

```bash
npm run build
node --test test/shortform-director-run-storage.test.js
node --test test/shortform-director-research-orchestrator.test.js
```

- [ ] **Step 5: 조건부 체크포인트**

사용자가 commit을 요청한 경우에만 run 상태 관련 파일만 stage하고
`feat(shortform-director): add resumable reference selection state`로 commit한다.

---

## Task 2. 첫 조사 승인을 discovery 전용 계약으로 축소

**Files**

- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/domain/research-cost-estimate.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-research-preflight.service.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/presentation/dto/start-shortform-director-research.dto.ts`
- Test: `desktop/clipper_nestjs/test/shortform-director-research-cost-estimate.test.js`

- [ ] **Step 1: discovery 호출 상한 테스트 작성**

첫 preflight의 정확한 계약을 다음으로 고정한다.

| provider | 작업 | 최대 호출 |
|---|---|---:|
| Google Trends | KR RSS | 1 |
| Naver | 뉴스 date/sim 3 query + DataLab | 7 |
| YouTube | viewCount 1 + relevance 1 + videos.list 1 | 3 |
| OpenAI | query plan + source normalization | 2 |
| Gemini | 없음 | 0 |

`gemini`는 첫 preflight의 required credential과 provider list에서 제외한다. approval
version은 `research-discovery-cost-2026-07-29.v1`, 가격 기준일은 `2026-07-29`로
바꾼다.

YouTube의 2026-06 이후 granular quota를 하나의 숫자로 합치지 않는다.

- `search.list`: Search Queries bucket에서 2/100 calls
- `videos.list`: 일반 YouTube Data quota 1 unit

기존 UI의 `YouTube 최대 12 quota units` 문구와 단일 `maxQuotaUnits`는
`quotaBuckets` 표시로 교체한다.

- [ ] **Step 2: RED 확인**

```bash
cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/shortform-director-research-cost-estimate.test.js
```

- [ ] **Step 3: estimate와 approval hash 입력 구현**

기존 topic synthesis와 metadata-only Gemini 비용을 제거한다. OpenAI discovery 비용은
`gpt-5.4-nano` 2회의 현재 catalog 단가와 보수적 token cap만 포함한다.

- [ ] **Step 4: GREEN 확인**

```bash
npm run build
node --test test/shortform-director-research-cost-estimate.test.js
```

- [ ] **Step 5: 조건부 체크포인트**

사용자가 요청한 경우에만 `refactor(shortform-director): split discovery cost approval`로
commit한다.

---

## Task 3. YouTube 원시 결과 12개에서 적격 후보 최대 6개 생성

**Files**

- Add: `desktop/clipper_nestjs/src/modules/shortform-director/domain/reference-candidate.ts`
- Add: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-reference-candidate.collector.ts`
- Add: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-reference-candidate.ranker.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-research-source.collector.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-research-input.builder.ts`
- Modify: `web/clipper_web_api/src/modules/shortform-director-research/application/youtube-data-provider.service.ts`
- Test: `desktop/clipper_nestjs/test/shortform-director-reference-candidates.test.js`
- Test: `web/clipper_web_api/src/modules/shortform-director-research/application/youtube-data-provider.service.spec.ts`

- [ ] **Step 1: 후보 필터·점수 테스트 작성**

fixture는 provider를 성공한 것처럼 런타임에서 쓰지 않고 단위 parser 입력으로만 쓴다.
다음을 검증한다.

- 같은 query로 `viewCount`, `relevance`를 각 1회, `maxResults: 6`으로 요청한다.
- `videos.list`는 중복 제거된 최대 12개 ID를 한 번에 요청한다.
- 30일 범위 밖, 3분 초과, 비공개/처리 불가, exact/fuzzy 재업로드를 제외한다.
- 한 채널은 최종 6개 중 최대 2개다.
- 조회수/좋아요/댓글이 없으면 `null`이며 공유 수는 항상 `null`이다.
- `viewsPerHour`, engagement rate, recency, query relevance, relative performance,
  shortform fit을 각각 보존한다.
- 최종 후보는 최대 6개, 추천은 서로 다른 채널을 우선해 정확히 3개다.
- 적격 후보가 3개 미만이면 `availability: "insufficient"`다.

- [ ] **Step 2: RED 확인**

```bash
cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/shortform-director-reference-candidates.test.js

cd /Users/jina/project/adlight/web/clipper_web_api
npm test -- --runInBand youtube-data-provider.service.spec.ts
```

- [ ] **Step 3: 수집 API 분리**

collector를 다음 세 책임으로 나눈다.

```ts
collectMarketSources(queries, window, credentials, bearerToken, record)
collectYoutubeCandidateSources(primaryQuery, window, credential, bearerToken, record)
collectSelectedVideoComments(videoIds, credential, bearerToken, record)
```

Naver는 최대 3 query를 계속 병렬 발견원으로 사용한다. YouTube는
`focusKeyword ?? queries[0]` 하나만 두 lane에서 사용한다. 초기 discovery에서는
댓글을 호출하지 않는다.

- [ ] **Step 4: deterministic ranker 구현**

단일 불투명 `viralScore`만 저장하지 않는다. 각 0–1 구성 점수와 사람이 읽는 추천 이유를
저장한다. tie-break는 `recency → viewsPerHour → videoId`로 고정해 같은 입력이 같은
추천을 만들게 한다.

- [ ] **Step 5: GREEN 확인**

```bash
cd /Users/jina/project/adlight/web/clipper_web_api
npm test -- --runInBand youtube-data-provider.service.spec.ts
npm run build

cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/shortform-director-reference-candidates.test.js
```

- [ ] **Step 6: 조건부 체크포인트**

사용자가 요청한 경우에만 각 저장소에서 관련 파일을
`feat(shortform-director): collect bounded YouTube reference candidates`로 commit한다.

---

## Task 4. discovery를 후보 게시 후 안전하게 멈추는 facade로 분리

**Files**

- Add: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-research-discovery.service.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-research.service.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-research-artifact.service.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-research.models.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/presentation/shortform-director-research.controller.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/shortform-director.module.ts`
- Test: `desktop/clipper_nestjs/test/shortform-director-research-orchestrator.test.js`

- [ ] **Step 1: 단계 중단 테스트 작성**

첫 조사 실행이 다음 순서로 끝나는지 검증한다.

```text
profile/approval
→ Google Trends
→ query plan
→ Naver + YouTube two lanes/details
→ source normalization
→ candidates/recommendation artifact
→ parent awaiting_reference_selection
```

Gemini, comments, reference pattern synthesis, topic synthesis는 이 단계에서 호출되면
테스트를 실패시킨다. 후보가 3개 미만이면 candidate artifact를 보존하고 parent를
`partial`로 끝내며 Gemini 호출은 0회여야 한다.

- [ ] **Step 2: RED 확인**

```bash
cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/shortform-director-research-orchestrator.test.js
```

- [ ] **Step 3: discovery service 추출**

기존 `ShortformDirectorResearchService`는 HTTP facade와 run 조회만 맡긴다.
`ShortformDirectorResearchDiscoveryService.start()`가 실제 첫 단계를 실행한다.
기존 `youtube-reference-analysis`와 즉시 topic synthesis 코드를 제거한다.

- [ ] **Step 4: typed candidate reader와 endpoint 구현**

```http
GET /projects/shortform-director/research/runs/:runId/reference-candidates
```

응답은 `ShortformDirectorReferenceCandidatesV1`이며 candidate snapshot ID, 추천 3개,
각 점수 구성, source artifact IDs를 포함한다.

- [ ] **Step 5: GREEN 확인**

```bash
npm run build
node --test test/shortform-director-research-orchestrator.test.js
node --test test/shortform-director-source-failure-boundary.test.js
```

- [ ] **Step 6: 조건부 체크포인트**

사용자가 요청한 경우에만
`refactor(shortform-director): pause research for reference selection`로 commit한다.

---

## Task 5. 정확히 3개를 고정하는 선택 revision 구현

**Files**

- Add: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-reference-selection.service.ts`
- Add: `desktop/clipper_nestjs/src/modules/shortform-director/presentation/dto/update-shortform-director-reference-selection.dto.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/domain/reference-candidate.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-research-artifact.service.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/presentation/shortform-director-research.controller.ts`
- Test: `desktop/clipper_nestjs/test/shortform-director-reference-selection.test.js`

- [ ] **Step 1: 선택 불변식 테스트 작성**

- parent가 `awaiting_reference_selection`이어야 한다.
- candidate snapshot ID가 현재 run의 최신 snapshot이어야 한다.
- `selectedVideoIds`는 정확히 3개, 중복 없음, 모두 적격 후보여야 한다.
- 같은 선택도 새 revision으로 append하며 기존 JSON을 덮어쓰지 않는다.
- 추천 3개와 사용자가 바꾼 3개를 모두 저장할 수 있다.
- terminal/다른 사용자의 run은 변경할 수 없다.

- [ ] **Step 2: RED 확인**

```bash
cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/shortform-director-reference-selection.test.js
```

- [ ] **Step 3: endpoint 구현**

```http
PUT /projects/shortform-director/research/runs/:runId/reference-selection
Content-Type: application/json

{
  "candidateSnapshotId": "...",
  "selectedVideoIds": ["...", "...", "..."]
}
```

응답은 immutable `selectionRevisionId`, selected candidates, selectedAt을 반환한다.

- [ ] **Step 4: GREEN 확인**

```bash
npm run build
node --test test/shortform-director-reference-selection.test.js
```

- [ ] **Step 5: 조건부 체크포인트**

사용자가 요청한 경우에만
`feat(shortform-director): persist reference selection revisions`로 commit한다.

---

## Task 6. 선택 영상 기준 두 번째 비용 승인 계약 구현

**Files**

- Add: `desktop/clipper_nestjs/src/modules/shortform-director/domain/reference-analysis-cost-estimate.ts`
- Add: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-reference-analysis-preflight.service.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-research.models.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/presentation/shortform-director-research.controller.ts`
- Test: `desktop/clipper_nestjs/test/shortform-director-reference-analysis-cost.test.js`

- [ ] **Step 1: 선택·credential 결합 quote 테스트 작성**

`reference-analysis-cost-2026-07-29.v1` preflight는 다음을 포함한다.

- 선택한 video ID/title/duration 3개
- Gemini `gemini-3.6-flash`: 기본 3회, 영상별 전체 재시도 상한 1회를 포함해 최대 6회
- 기존 로컬 `faster-whisper-small`: 자막 부재 영상 최대 3건, 외부 API 호출·비용 없음
- OpenAI `gpt-5.6-luna`: reference pattern synthesis 1회, topic synthesis 1회
- YouTube comments: 선택 영상당 최대 1회, 총 3회
- Gemini Standard `USD 1.50/MTok input`, `USD 7.50/MTok output+thinking`
- Gemini default video estimate `300 tokens/sec`
- 가격 기준일 `2026-07-29`

YouTube 댓글 3회는 일반 YouTube Data quota 3 units로 별도 표시하고 Gemini/OpenAI의
USD 예상 비용과 섞지 않는다.

이미 같은 parent run에서 validation을 통과한 영상은 `reused: true`로 표시하고
Gemini와 로컬 STT 예상 작업에서 제외한다.

- [ ] **Step 2: RED 확인**

```bash
cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/shortform-director-reference-analysis-cost.test.js
```

- [ ] **Step 3: approval hash 구현**

approval ID는 selection revision, 세 video ID/duration, retry cap, model IDs, 가격,
YouTube/OpenAI/Gemini credential ID와 revision을 모두 hash한다. 선택이나 credential이
달라지면 기존 승인은 409로 거절한다.

`faster-whisper-small`은 로컬 모델이므로 credential hash에는 들어가지 않는다. 다만
preflight에는 `local`, 모델 ID, 자막 부재 시 최대 처리 영상 수를 정보로 보여준다.

- [ ] **Step 4: endpoint 구현**

```http
GET /projects/shortform-director/research/runs/:runId/reference-analysis/preflight?selectionRevisionId=...
```

- [ ] **Step 5: GREEN 확인**

```bash
npm run build
node --test test/shortform-director-reference-analysis-cost.test.js
```

- [ ] **Step 6: 조건부 체크포인트**

사용자가 요청한 경우에만
`feat(shortform-director): quote selected reference video analysis`로 commit한다.

---

## Task 7. yt-dlp·FFmpeg·ffprobe 실제 전처리 구현

**Files**

- Modify: `desktop/clipper_nestjs/src/modules/sources/application/source.service.ts`
- Modify: `desktop/clipper_nestjs/src/modules/sources/domain/source.model.ts`
- Add: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-reference-media.preprocessor.ts`
- Add: `desktop/clipper_nestjs/src/modules/shortform-director/infrastructure/shortform-director-reference-media-tool.runner.ts`
- Add: `desktop/clipper_nestjs/src/modules/shortform-director/infrastructure/local-shortform-director-reference-media.storage.ts`
- Test: `desktop/clipper_nestjs/test/shortform-director-reference-media.test.js`

- [ ] **Step 1: VTT와 로컬 계산 RED 테스트 작성**

다음을 검증한다.

- 기존 `sources/youtube/<videoId>` MP4 cache hit를 재사용한다.
- 제작자 VTT가 있으면 자동 VTT보다 우선한다.
- VTT cue timestamp와 중복 롤링 자막을 정규화한다.
- 자막이 없으면 다운로드된 MP4의 local STT가 필요하다고 표시한다.
- ffprobe duration/width/height를 숫자로 파싱한다.
- FFmpeg가 전체 영상을 디코딩한 scene score/timestamp를 수집한다.
- 첫 0/0.5/1/2/3초, 큰 컷 전후, 중간, 마지막 CTA를 포함해 로컬 최대 24장,
  provider 전송 최대 12장을 선택한다.
- frame/media JSON에는 bytes/base64가 없고 SHA-256과 상대 경로만 있다.

- [ ] **Step 2: RED 확인**

```bash
cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/shortform-director-reference-media.test.js
```

- [ ] **Step 3: SourceService의 좁은 획득 API 구현**

다음 공개 method만 추가하고 yt-dlp 인증·쿠키 fallback을 복제하지 않는다.

```ts
prepareYoutubeReference(
  source: YoutubeUrlSourceInput,
  options?: SourcePrepareOptions,
): Promise<PreparedYoutubeReferenceSource>
```

내부에서는 기존 `ingest()`와 `runYtdlp()`를 재사용한다. creator caption을 먼저
`--write-subs --no-write-auto-subs`로 시도하고, 없을 때만 auto caption을
`--write-auto-subs --no-write-subs`로 받는다.

- [ ] **Step 4: FFmpeg 서비스 분리 구현**

`ReferenceMediaToolRunner`는 process 실행과 stderr timestamp parsing만 맡고,
`ReferenceMediaPreprocessor`는 선택·전처리 순서를 맡는다. 한 클래스에 yt-dlp,
artifact publication, provider 호출까지 넣지 않는다.

- [ ] **Step 5: 실제 FFmpeg GREEN 확인**

테스트가 임시 디렉터리의 짧은 합성 clip을 실제 ffmpeg로 만들고 실제 ffprobe/scene
분석을 실행하게 한다.

```bash
npm run build
node --test test/shortform-director-reference-media.test.js
```

- [ ] **Step 6: 조건부 체크포인트**

사용자가 요청한 경우에만
`feat(shortform-director): preprocess real reference video media`로 commit한다.

---

## Task 8. 대사 하이라이트의 기존 로컬 STT를 AI Director에서 재사용

**Files**

- Modify: `desktop/clipper_python/plugins/dialog_highlight/dialog_highlight/services/stage_contracts.py`
- Modify: `desktop/clipper_python/plugins/dialog_highlight/dialog_highlight/services/stage_runner.py`
- Add: `desktop/clipper_python/tests/test_dialog_transcribe_stage.py`
- Modify: `desktop/clipper_python/tests/test_dialog_stage_contracts.py`
- Add: `desktop/clipper_nestjs/src/modules/plugins/application/local-plugin-job.runner.ts`
- Modify: `desktop/clipper_nestjs/src/modules/dialog-highlight/application/dialog-highlight-python-stage.runner.ts`
- Add: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-reference-local-stt.client.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/shortform-director.module.ts`
- Add: `desktop/clipper_nestjs/test/shortform-director-reference-local-stt.test.js`
- Modify matching dialog-highlight stage runner tests

- [ ] **Step 1: Python stage RED 테스트 작성**

`transcribe_media`는 입력 MP4와 output root를 받고 다음만 수행해야 한다.

- 기존 `stt_worker.run_stt(..., model_size="small")`를 호출한다.
- `json/stt.json`에 기존 schema의 실제 segment/word timestamp를 쓴다.
- OpenCLIP, OCR, shot/audio embedding, provider API를 호출하지 않는다.
- 기존 `analyze_media`와 대사 하이라이트 동작은 바꾸지 않는다.

- [ ] **Step 2: Python RED 확인**

```bash
cd /Users/jina/project/adlight/desktop/clipper_python
uv run pytest tests/test_dialog_transcribe_stage.py tests/test_dialog_stage_contracts.py -q
```

- [ ] **Step 3: 기존 STT를 호출하는 좁은 stage 구현**

`stage_runner.py`가 같은 `run_stt`를 호출하게 하고 결과에는 stage, output root,
`stt.json` 상대 경로와 모델 ID만 반환한다. transcript 내용은 이미 쓰인 JSON 파일에서
읽으며 별도 전사 구현을 만들지 않는다.

- [ ] **Step 4: Nest 공통 local plugin runner RED 테스트 작성**

현재 `DialogHighlightPythonStageRunner` 안에 있는 `PluginHost.ensureStarted`,
`POST /jobs`, WebSocket progress/completion, cancel 로직을 provider-free 공통 runner로
추출한다. 다음을 검증한다.

- 기존 대사 하이라이트 runner의 동작과 progress mapping이 유지된다.
- AI Director client는 `dialog_highlight/transcribe_media`만 호출한다.
- AI Director 경로는 `DialogHighlightWorkflowExecutor.startBillableOperation`을 호출하지
  않으며 operation/credit ID를 만들지 않는다.
- 취소·plugin 오류·깨진 STT JSON은 성공으로 저장되지 않는다.

- [ ] **Step 5: Nest RED 확인**

```bash
cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/shortform-director-reference-local-stt.test.js \
  test/dialog-highlight-python-stage-runner.test.js
```

- [ ] **Step 6: 공통 runner와 AI Director adapter 구현**

공통 runner는 plugin name, job ID, params, abort signal, progress callback만 받는다.
AI Director adapter가 결과 파일을 읽어 segment/word timestamp를 transcript artifact로
정규화한다. Python 구현 세부와 billing workflow를 shortform orchestrator에 노출하지
않는다.

- [ ] **Step 7: GREEN 확인**

```bash
cd /Users/jina/project/adlight/desktop/clipper_python
uv run pytest tests/test_dialog_transcribe_stage.py tests/test_dialog_stage_contracts.py -q

cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/shortform-director-reference-local-stt.test.js \
  test/dialog-highlight-python-stage-runner.test.js
```

- [ ] **Step 8: 조건부 체크포인트**

사용자가 요청한 경우에만 저장소별로
`feat(dialog-highlight): expose reusable local transcription stage`와
`feat(shortform-director): reuse local dialog transcription`으로 commit한다.

---

## Task 9. Web API Gemini 실제 영상 정밀 분석 endpoint 구현

**Files**

- Modify first: `web/clipper_web_api/docs/api/openapi.yaml`
- Modify: `web/clipper_web_api/src/modules/shortform-director-reference-analysis/domain/reference-analysis.contract.ts`
- Modify: `web/clipper_web_api/src/modules/shortform-director-reference-analysis/domain/reference-analysis.transport.ts`
- Add: `web/clipper_web_api/src/modules/shortform-director-reference-analysis/application/reference-analysis.prompt.ts`
- Add: `web/clipper_web_api/src/modules/shortform-director-reference-analysis/application/shortform-director-reference-analysis.service.ts`
- Add: `web/clipper_web_api/src/modules/shortform-director-reference-analysis/infrastructure/google-reference-video-analysis.transport.ts`
- Modify: `web/clipper_web_api/src/modules/shortform-director-reference-analysis/presentation/shortform-director-reference-analysis.controller.ts`
- Add matching `.spec.ts` and OpenAPI spec

- [ ] **Step 1: 실제 request shape RED 테스트 작성**

```http
POST /shortform-director/reference-video-analyses
Content-Type: multipart/form-data
```

fields:

- `request`: public YouTube URL, video ID, duration, profile context, metrics/comments,
  transcript, local cut summary, frame ID/timestamp, expected Gemini credential의 JSON
- `frames`: JPEG 최대 12개, 파일당 최대 512 KiB

transport test는 정확히 다음 provider body를 요구한다.

```ts
{
  model: 'gemini-3.6-flash',
  input: [
    { type: 'video', uri: 'https://www.youtube.com/watch?v=...' },
    // selected frame image inputs
    { type: 'text', text: 'versioned compact prompt' },
  ],
  response_format: {
    type: 'text',
    mime_type: 'application/json',
    schema: perVideoSchema,
  },
}
```

한 요청에 video input이 둘 이상이거나 Google Search grounding이 있으면 실패한다.

- [ ] **Step 2: RED 확인**

```bash
cd /Users/jina/project/adlight/web/clipper_web_api
npm test -- --runInBand google-reference-video-analysis
npm test -- --runInBand shortform-director-reference-analysis
```

- [ ] **Step 3: compact semantic schema 구현**

provider 출력은 hook, scroll stopper, mechanics, belief contrast, structure, on-screen text,
video claims, reusable pattern, confidence, limitations만 담는다. duration/cut count/shot
통계는 provider schema에 두지 않는다.

- [ ] **Step 4: Interactions transport와 안전한 audit 구현**

REST 응답의 `steps[].content[].text`를 파싱하고 structured JSON을 즉시 검증한다.
audit에는 status, request ID, model, credential ID/revision, prompt template version,
전송한 text, media ref 목록, usage, latency만 남긴다. provider response text/raw body는
audit에 넣지 않는다.

영상별 전체 provider attempt는 최대 2회다. 첫 429/5xx 또는 schema parse 실패에만 한
번 재시도하며 다른 이유로 세 번째 호출을 만들지 않는다.

- [ ] **Step 5: 오류 매핑 테스트**

- provider 400 → safe 502 +
  `SHORTFORM_DIRECTOR_REFERENCE_ANALYSIS_PROVIDER_INVALID_ARGUMENT`
- provider 429 → 429 + retryable code
- timeout → 504
- public YouTube URI 처리 불가 → 교체 가능한 candidate failure
- output schema invalid after second attempt → 502, parsed success 없음

- [ ] **Step 6: GREEN 확인**

```bash
npm test -- --runInBand shortform-director-reference-analysis
npm test -- --runInBand google-reference-video-analysis
npm test -- --runInBand shortform-director-reference-analysis.openapi
npm run build
```

- [ ] **Step 7: 조건부 체크포인트**

사용자가 요청한 경우에만
`feat(shortform-director): analyze real YouTube videos with Gemini`로 commit한다.

---

## Task 10. Desktop multipart client와 media artifact 공개 경계 구현

**Files**

- Modify: `desktop/clipper_nestjs/src/core/web-api/web-api-client.service.ts`
- Add: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-reference-analysis-web-api.client.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/infrastructure/local-shortform-director-reference-media.storage.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/presentation/shortform-director-research.controller.ts`
- Test: `desktop/clipper_nestjs/test/web-api-client.test.js`
- Test: `desktop/clipper_nestjs/test/shortform-director-reference-analysis-client.test.js`

- [ ] **Step 1: multipart RED 테스트 작성**

- bearer token을 보낸다.
- `FormData`의 boundary를 fetch가 설정하게 두고 JSON `Content-Type`을 강제로 넣지 않는다.
- frame bytes가 오류 본문이나 log에 포함되지 않는다.
- timeout/401/403/409/429/5xx는 기존 `WebApiClient` 오류 체계를 유지한다.

- [ ] **Step 2: RED 확인**

```bash
cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/web-api-client.test.js
node --test test/shortform-director-reference-analysis-client.test.js
```

- [ ] **Step 3: 좁은 multipart API 구현**

```ts
postMultipart<T>(
  path: string,
  form: FormData,
  options?: PostMultipartOptions,
): Promise<T>
```

`ReferenceAnalysisWebApiClient`만 이 method로 Gemini video analysis를 호출한다.
로컬 STT는 Web API를 거치지 않는다.

- [ ] **Step 4: 근거 frame endpoint 구현**

```http
GET /projects/shortform-director/research/runs/:runId/reference-media/:videoId/frames/:frameId
```

owner/run/video/frame manifest를 모두 확인한 후에만 JPEG를 반환한다. 임의 절대 경로나
`..` 상대 경로를 받을 수 있는 query API를 만들지 않는다.

- [ ] **Step 5: GREEN 확인**

```bash
npm run build
node --test test/web-api-client.test.js
node --test test/shortform-director-reference-analysis-client.test.js
```

- [ ] **Step 6: 조건부 체크포인트**

사용자가 요청한 경우에만
`feat(shortform-director): upload bounded reference evidence`로 commit한다.

---

## Task 11. Gemini 의미 결과와 로컬 사실을 조립·검증

**Files**

- Add: `desktop/clipper_nestjs/src/modules/shortform-director/domain/reference-analysis.ts`
- Add: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-reference-analysis.validator.ts`
- Test: `desktop/clipper_nestjs/test/shortform-director-reference-analysis-validation.test.js`

- [ ] **Step 1: validator RED 테스트 작성**

다음을 각각 거절한다.

- duration보다 뒤의 structure/on-screen-text timestamp
- `startMs >= endMs`
- 순서가 뒤집히거나 겹치는 structure
- manifest에 없는 transcript/frame/scene evidence ref
- transcript에 실제로 없는 spoken hook 직접 문구
- 외부 evidence 없이 `verified` 또는 `contradicted`로 표시한 video claim
- provider가 만든 cut count를 로컬 값 대신 사용한 결과

Revid 예시의 `duration 1:21`인데 `CTA 1:59`인 결과를 회귀 fixture로 넣고 반드시
rejected-analysis가 되게 한다.

- [ ] **Step 2: RED 확인**

```bash
cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/shortform-director-reference-analysis-validation.test.js
```

- [ ] **Step 3: assembler와 validator 구현**

`ReferenceVideoAnalysisV1`의 pacing 숫자는 FFmpeg manifest에서 복사하고 Gemini에는
interpretation만 맡긴다. evidence ref는 `<artifactId>#<itemId>` 형식으로 정규화한다.
검증 실패 시 parsed 결과를 삭제하지 않고 rejected artifact와 issue 목록을 만든다.

- [ ] **Step 4: GREEN 확인**

```bash
npm run build
node --test test/shortform-director-reference-analysis-validation.test.js
```

- [ ] **Step 5: 조건부 체크포인트**

사용자가 요청한 경우에만
`feat(shortform-director): validate reference analysis evidence`로 commit한다.

---

## Task 12. 세 영상의 독립 자식 run과 실패 후 교체·재사용 구현

**Files**

- Add: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-reference-analysis.orchestrator.ts`
- Add: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-reference-analysis.runner.ts`
- Add: `desktop/clipper_nestjs/src/modules/shortform-director/presentation/dto/start-shortform-director-reference-analysis.dto.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-research-artifact.service.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/presentation/shortform-director-research.controller.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/shortform-director.module.ts`
- Test: `desktop/clipper_nestjs/test/shortform-director-reference-analysis-orchestrator.test.js`

- [ ] **Step 1: 승인·자식 run RED 테스트 작성**

- 승인 ID/version/selection/credential가 일치하지 않으면 child를 만들지 않는다.
- 승인되면 `reference-analysis` child run을 만들고 parent `childRunIds`에 붙인다.
- HTTP POST는 child run ID를 즉시 반환하고 runner가 비동기로 실행한다.
- 각 영상은 acquire → caption/local STT → FFmpeg → Gemini → validate → persist 순이다.
- 영상 A 실패가 B/C 성공 artifact를 지우지 않는다.
- 세 개 중 하나가 실패하면 child는 `partial`, parent는
  `awaiting_reference_selection`에 남는다.
- 다음 selection에서 이미 통과한 A/B는 provider를 다시 부르지 않고
  `reference-analysis-reuse` artifact로 참조한다.
- 앱 시작 recovery는 running child만 failed 처리하고 awaiting parent는 보존한다.

- [ ] **Step 2: RED 확인**

```bash
cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/shortform-director-reference-analysis-orchestrator.test.js
```

- [ ] **Step 3: start endpoint와 scheduler port 구현**

```http
POST /projects/shortform-director/research/runs/:runId/reference-analysis

{
  "selectionRevisionId": "...",
  "approvalVersion": "reference-analysis-cost-2026-07-29.v1",
  "approvalId": "...",
  "confirmed": true
}
```

controller는 202와 child run을 반환한다. runner는 in-memory 중복 실행 guard를 두고,
모든 상태 변화와 progress를 JSON artifact로 먼저 저장한 뒤 UI가 poll하게 한다.

- [ ] **Step 4: 조회 endpoint 구현**

```http
GET /projects/shortform-director/research/runs/:runId/reference-analysis/attempts
GET /projects/shortform-director/research/reference-analysis/attempts/:attemptRunId
GET /projects/shortform-director/research/runs/:runId/reference-analyses
```

- [ ] **Step 5: GREEN 확인**

```bash
npm run build
node --test test/shortform-director-reference-analysis-orchestrator.test.js
node --test test/shortform-director-run-storage.test.js
```

- [ ] **Step 6: 조건부 체크포인트**

사용자가 요청한 경우에만
`feat(shortform-director): run replaceable reference analyses`로 commit한다.

---

## Task 13. 세 분석 종합과 topic 생성 재개

**Files**

- Modify: `web/clipper_web_api/src/modules/shortform-director-inference/domain/shortform-director-inference.contract.ts`
- Modify: `web/clipper_web_api/src/modules/shortform-director-inference/domain/shortform-director-model-catalog.ts`
- Modify: `web/clipper_web_api/src/modules/shortform-director-inference/application/shortform-director-inference.prompt.ts`
- Modify matching inference specs
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-inference-response.projector.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-research-topic.builder.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-reference-analysis.orchestrator.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-research.service.ts`
- Test: `desktop/clipper_nestjs/test/shortform-director-reference-analysis-orchestrator.test.js`
- Test: `desktop/clipper_nestjs/test/shortform-director-research-orchestrator.test.js`

- [ ] **Step 1: 3-of-3 gate RED 테스트 작성**

- validation passed 분석이 정확히 3개가 아니면 pattern/topic inference는 0회다.
- 정확히 3개면 `reference-pattern-synthesis` 1회 후 `topic-synthesis` 1회다.
- pattern의 모든 evidence ID가 세 analysis 또는 market source에 존재해야 한다.
- 원본 문구 복제 금지 요소를 저장한다.
- topic은 market/audience/reference evidence를 모두 연결한다.
- 완료 시 parent를 `running`으로 재개한 뒤 `succeeded` 또는 discovery optional failure가
  있었으면 `partial`로 terminal 전환한다.

- [ ] **Step 2: RED 확인**

```bash
cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/shortform-director-reference-analysis-orchestrator.test.js
node --test test/shortform-director-research-orchestrator.test.js
```

- [ ] **Step 3: inference purpose 교체**

공용 text inference에서 `youtube-reference-analysis`를 제거한다. 대신
`reference-pattern-synthesis`를 `gpt-5.6-luna`에 매핑한다. 과거 purpose의 거대한
multi-video Google schema와 metadata-only prompt가 active catalog에 남지 않게 한다.

- [ ] **Step 4: reference pattern 및 topic publication 구현**

세 분석을 `reference-patterns.json`으로 게시한 뒤 기존 topic builder가 이를 입력으로
사용하게 한다. topic 이후 기존 영상 후보 10개 생성 계약은 바꾸지 않는다.

- [ ] **Step 5: GREEN 확인**

```bash
cd /Users/jina/project/adlight/web/clipper_web_api
npm test -- --runInBand shortform-director-inference
npm run build

cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/shortform-director-reference-analysis-orchestrator.test.js
node --test test/shortform-director-research-orchestrator.test.js
```

- [ ] **Step 6: 조건부 체크포인트**

사용자가 요청한 경우에만
`feat(shortform-director): synthesize validated reference patterns`로 commit한다.

---

## Task 14. Angular 계약·gateway·store에 선택과 polling 연결

**Files**

- Modify: `desktop/clipper_angular/src/features/shortform-director/models/shortform-director-research.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-research.gateway.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-research.service.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/state/shortform-director-research.store.ts`
- Test: `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-research.service.spec.ts`
- Test: `desktop/clipper_angular/src/features/shortform-director/state/shortform-director-research.store.spec.ts`

- [ ] **Step 1: gateway/store RED 테스트 작성**

- awaiting run 선택 시 topic 대신 reference candidates를 로드한다.
- 추천 3개를 초기 선택으로 둔다.
- 정확히 3개일 때 selection revision을 저장한다.
- 해당 revision의 preflight만 비용 승인에 쓴다.
- 근거 frame은 인증된 `HttpClient`로 Blob을 받아 object URL로 표시하고 해제 시 revoke한다.
- analysis 시작 후 child attempt를 poll한다.
- component/store destroy 시 polling을 중단한다.
- child partial이면 성공한 분석은 남기고 후보 교체 UI로 돌아간다.
- parent terminal 후 topic을 로드한다.

- [ ] **Step 2: RED 확인**

```bash
cd /Users/jina/project/adlight/desktop/clipper_angular
./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless \
  --include='src/features/shortform-director/services/shortform-director-research.service.spec.ts' \
  --include='src/features/shortform-director/state/shortform-director-research.store.spec.ts'
```

- [ ] **Step 3: model/gateway/store 구현**

store에는 candidates, selected IDs, selection revision, reference preflight, attempts,
analyses를 각각 별도 signal로 둔다. `ideas-page`가 HTTP 세부 절차를 직접 조립하지 않게
한다.

- [ ] **Step 4: GREEN 확인**

```bash
./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless \
  --include='src/features/shortform-director/services/shortform-director-research.service.spec.ts' \
  --include='src/features/shortform-director/state/shortform-director-research.store.spec.ts'
npm run build
```

- [ ] **Step 5: 조건부 체크포인트**

사용자가 요청한 경우에만
`feat(shortform-director): manage reference analysis state`로 commit한다.

---

## Task 15. 최대 6개 후보와 추천 3개 교체 UI 구현

**Files**

- Add: `desktop/clipper_angular/src/features/shortform-director/components/research-reference-candidate-list/research-reference-candidate-list.component.ts`
- Add corresponding `.html`, `.scss`, `.spec.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/pages/ideas-page/ideas-page.component.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/pages/ideas-page/ideas-page.component.html`
- Modify: `desktop/clipper_angular/src/features/shortform-director/pages/ideas-page/ideas-page.component.scss`
- Test: `desktop/clipper_angular/src/features/shortform-director/pages/ideas-page/ideas-page.component.spec.ts`

- [ ] **Step 1: 후보 UX RED 테스트 작성**

카드는 다음을 보여준다.

- 썸네일, 제목, 채널, 게시 시각, 길이
- 조회수, 좋아요, 댓글, 참여율, 시간당 조회수
- shares는 숫자 0이 아니라 `—`
- current-popular/current-relevant lane
- `AI 디렉터 추천` 표시와 추천 이유
- 선택 3/3 상태
- `YouTube에서 보기`
- `수집 근거 보기`

사용자는 추천 항목을 해제하고 다른 후보를 선택할 수 있다. 선택이 정확히 3개가 아니면
`분석 비용 확인` 버튼은 비활성화된다.

- [ ] **Step 2: RED 확인**

```bash
cd /Users/jina/project/adlight/desktop/clipper_angular
./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless \
  --include='src/features/shortform-director/components/research-reference-candidate-list/research-reference-candidate-list.component.spec.ts' \
  --include='src/features/shortform-director/pages/ideas-page/ideas-page.component.spec.ts'
```

- [ ] **Step 3: standalone component 구현**

접근 가능한 checkbox/label을 사용하고 모바일에서는 표가 아니라 세로 카드로 보이게 한다.
후보 컴포넌트는 selection event만 내보내고 HTTP를 직접 호출하지 않는다.

- [ ] **Step 4: GREEN 확인**

```bash
./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless \
  --include='src/features/shortform-director/components/research-reference-candidate-list/research-reference-candidate-list.component.spec.ts' \
  --include='src/features/shortform-director/pages/ideas-page/ideas-page.component.spec.ts'
npm run build
```

- [ ] **Step 5: 조건부 체크포인트**

사용자가 요청한 경우에만
`feat(shortform-director): let users choose reference videos`로 commit한다.

---

## Task 16. 두 번째 승인·진행 상태·“왜 효과가 있었나” UI 구현

**Files**

- Add: `desktop/clipper_angular/src/features/shortform-director/components/research-reference-analysis-preflight/*`
- Add: `desktop/clipper_angular/src/features/shortform-director/components/research-reference-analysis-progress/*`
- Add: `desktop/clipper_angular/src/features/shortform-director/components/research-reference-analysis-detail/*`
- Modify: `desktop/clipper_angular/src/features/shortform-director/pages/ideas-page/ideas-page.component.{ts,html,scss,spec.ts}`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/research-run-list/*`

- [ ] **Step 1: 승인 UI RED 테스트 작성**

승인 카드에는 선택 영상 3개, 길이, provider/model, 기본/최대 호출, 자막 부재 시
`faster-whisper-small` 로컬 처리 최대 건수와 외부 비용 없음, cross/topic synthesis,
최소/최대 비용, 가격 기준일, approval version을 모두 표시한다. generic confirm 문구만
띄우고 세부 내용을 숨기지 않는다.

- [ ] **Step 2: 진행/실패 UI RED 테스트 작성**

각 영상은 `획득 → 자막/로컬 STT → 컷/프레임 → Gemini → 검증 → 저장` 상태를 보여준다.
하나가 실패하면 성공한 두 개와 실패 이유를 유지하고 `다른 후보로 교체`를 제공한다.

- [ ] **Step 3: 분석 상세 RED 테스트 작성**

Revid에서 유용했던 다음 내용을 별도 상세 컴포넌트로 보여준다.

- spoken/visual hook와 formula
- scroll-stopper
- 작동 방식(mechanics)
- common belief / contrarian reality
- timestamped structure
- pacing
- on-screen text
- 재사용할 패턴과 복제하면 안 되는 요소
- confidence/limitations
- `근거 프레임·자막 보기`
- `provider 호출 과정 보기`

- [ ] **Step 4: RED 확인**

```bash
cd /Users/jina/project/adlight/desktop/clipper_angular
./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless \
  --include='src/features/shortform-director/components/research-reference-analysis-preflight/*.spec.ts' \
  --include='src/features/shortform-director/components/research-reference-analysis-progress/*.spec.ts' \
  --include='src/features/shortform-director/components/research-reference-analysis-detail/*.spec.ts' \
  --include='src/features/shortform-director/pages/ideas-page/ideas-page.component.spec.ts'
```

- [ ] **Step 5: 컴포넌트 분리 구현**

`ideas-page`에는 섹션 배치와 store method 호출만 둔다. 분석 상세에서 raw JSON을 직접
포맷하지 않고 기존 `ResearchArtifactPanel`을 재사용해 저장 artifact를 연다. frame은
보안 endpoint를 단순 `<img src>`로 직접 연결하지 않고 gateway의 인증된 Blob 요청을
사용하며 컴포넌트 destroy 때 모든 object URL을 해제한다.

- [ ] **Step 6: GREEN 확인**

```bash
./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless \
  --include='src/features/shortform-director/components/research-reference-analysis-preflight/*.spec.ts' \
  --include='src/features/shortform-director/components/research-reference-analysis-progress/*.spec.ts' \
  --include='src/features/shortform-director/components/research-reference-analysis-detail/*.spec.ts' \
  --include='src/features/shortform-director/pages/ideas-page/ideas-page.component.spec.ts'
npm run build
```

- [ ] **Step 7: 조건부 체크포인트**

사용자가 요청한 경우에만
`feat(shortform-director): show reference analysis evidence`로 commit한다.

---

## Task 17. 오류 문구·보안·전체 계약 회귀 검증

**Files**

- Modify: `desktop/clipper_angular/src/core/errors/error-catalog.ts`
- Modify: `desktop/clipper_angular/src/core/errors/error-catalog.spec.ts`
- Modify affected OpenAPI and security specs in all four repositories

- [ ] **Step 1: 사용자 오류 문구 테스트 작성**

다음 코드를 구분한다.

- 후보 부족
- selection 변경/만료
- credential 변경
- YouTube 다운로드/자막 실패
- Gemini public URI 처리 실패
- provider rate limit
- 분석 출력 검증 실패
- child interrupted

generic “일시적인 문제” 하나로만 보이지 않게 하되 secret/provider raw는 노출하지 않는다.

- [ ] **Step 2: 보안 RED 테스트 작성**

artifact와 HTTP 응답 전체를 재귀 검사해 다음이 없어야 한다.

- API key, bearer token, cookie
- Authorization/x-goog-api-key
- media/frame base64
- provider raw response/raw error body
- Clipper credit/operation run ID

- [ ] **Step 3: 오류 catalog와 redaction 구현**

실패 영상은 교체 가능한지, 재시도 가능한지, 관리자 credential 조치가 필요한지를
한국어 action 문구로 구분한다.

- [ ] **Step 4: repository별 전체 자동 검증**

```bash
cd /Users/jina/project/adlight/web/clipper_web_api
npm test -- --runInBand
npm run build

cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/shortform-director-*.test.js test/web-api-client.test.js

cd /Users/jina/project/adlight/desktop/clipper_python
uv run pytest tests/test_dialog_transcribe_stage.py tests/test_dialog_stage_contracts.py -q

cd /Users/jina/project/adlight/desktop/clipper_angular
./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless
npm run build
```

- [ ] **Step 5: 금지 회귀 검색**

```bash
cd /Users/jina/project/adlight
rg -n "youtube-reference-analysis|response\\.raw|operationRunId|credit|Remotion|remotion" \
  desktop/clipper_nestjs/src/modules/shortform-director \
  desktop/clipper_angular/src/features/shortform-director \
  web/clipper_web_api/src/modules/shortform-director-reference-analysis \
  web/clipper_web_api/src/modules/shortform-director-inference
```

허용된 과거 migration/다른 플러그인 결과가 아니라 새 reference 경로에서 발견되면
제거한다.

- [ ] **Step 6: diff 검토**

```bash
git -C /Users/jina/project/adlight/desktop/clipper_nestjs diff --check
git -C /Users/jina/project/adlight/desktop/clipper_python diff --check
git -C /Users/jina/project/adlight/desktop/clipper_angular diff --check
git -C /Users/jina/project/adlight/web/clipper_web_api diff --check
git -C /Users/jina/project/adlight/.codex diff --check
```

- [ ] **Step 7: 조건부 체크포인트**

사용자가 요청한 경우에만 저장소별 관련 변경을 나눠 commit한다. 기존 제작 모델·장면
수정 변경과 reference analysis 변경을 한 commit에 무리하게 섞지 않는다.

---

## Task 18. 명시적 승인 후 실제 end-to-end 검증

이 Task만 실제 provider 비용과 YouTube 다운로드가 발생한다. 자동 테스트가 모두
통과해도 바로 실행하지 않는다.

- [ ] **Step 1: 실행 직전 사용자에게 호출표 제시**

다음을 실제 UI preflight 값 그대로 보고한다.

- 선택한 운영 프로필과 focus keyword
- YouTube 후보 검색 2회/details 1회
- 선택한 영상 3개와 길이
- Gemini 기본 3회/최대 6회
- 실제 자막 유무에 따른 로컬 `faster-whisper-small` 처리 예상 0–3건과 외부 비용 없음
- reference pattern/topic synthesis 각 1회
- 예상 USD 최소/최대와 가격 기준일

- [ ] **Step 2: 사용자에게 실제 호출 승인 받기**

승인 전에는 Gemini, 로컬 STT, pattern/topic synthesis를 호출하지 않는다.

- [ ] **Step 3: 앱에서 실제 흐름 실행**

```text
운영 프로필
→ 아이디어 찾기
→ 첫 조사 승인
→ 실제 후보 최대 6개 확인
→ 추천 3개 검토/교체
→ 두 번째 비용 승인
→ 실제 영상 3개 정밀 분석
→ 근거·과정 확인
→ 최신 조사 주제 확인
→ 주제 선택
→ 영상 후보 10개 이상
→ 영상 제작
→ 기존 Jobs 큐
→ 기존 Projects 보관함에서 MP4 재생
```

- [ ] **Step 4: 로컬 저장을 직접 검증**

각 run의 JSON artifact에서 source call, selection revision, approval, transcript,
scene boundaries, keyframes manifest, provider call audit, parsed analysis, validation,
reference patterns, topics를 확인한다. MP4/WAV/JPEG는 JSON 안이 아니라 별도 파일이며
checksum과 일치해야 한다.

- [ ] **Step 5: 실제 품질 acceptance**

- 세 Gemini 요청이 실제 서로 다른 선택 영상 하나씩을 보았는가
- hook/structure timestamp가 영상 길이 안인가
- 첫 3초 프레임과 빠른 컷이 근거에 포함됐는가
- 영상 속 주장을 외부 검증 사실로 오인하지 않았는가
- 최근 시장 신호와 reference 형식이 topic에 함께 연결됐는가
- topic 하나당 제작 영상 후보가 최소 10개인가
- 최종 영상 장면별 asset/model 계보가 보이는가
- 최종 MP4가 기존 보관함에서 재생되는가

실패하면 어느 단계의 실제 artifact가 문제인지 특정하고, 같은 비용 호출을 무작정
반복하지 않는다.

---

## 3. 구현 완료 정의

다음 조건을 모두 만족해야 완료다.

1. 첫 조사 버튼은 metadata-only Gemini를 호출하지 않는다.
2. YouTube는 최대 12 raw ID, 최대 6 후보, 추천/선택 정확히 3개다.
3. 사용자는 추천 3개를 다른 후보로 교체할 수 있다.
4. 선택 영상과 비용을 확인하기 전에는 Gemini/로컬 STT가 실행되지 않는다.
5. Gemini는 실제 공개 YouTube video URI를 한 요청당 하나씩 처리한다.
6. 자막·전체 컷 분석·주요 프레임이 실제 로컬 미디어에서 만들어진다.
7. 영상 길이 밖 timestamp와 존재하지 않는 evidence가 게시되지 않는다.
8. 한 영상 실패 시 부모 조사와 성공 분석이 보존되고 후보 교체가 가능하다.
9. 세 개의 검증 통과 분석 전에는 공통 패턴과 topic을 만들지 않는다.
10. provider raw, API key, bearer token, base64 binary가 JSON에 없다.
11. AI Director 크레딧 차감이 없다.
12. 분석 결과와 근거·호출 과정이 Angular에서 확인된다.
13. 기존 topic → 후보 10개 이상 → 제작 → Jobs → 보관함 흐름이 실제 MP4까지 이어진다.
14. 네 저장소 build와 전체 관련 test가 통과한다.
15. 실제 provider 검증은 별도 비용표와 사용자 승인 뒤 수행했다.

---

## 4. 실행 방식

이 계획은 Task 1부터 순서대로 실행한다. Task 3의 Web API YouTube part 수정과 desktop
candidate parser처럼 독립적인 RED/GREEN 쌍만 병렬화할 수 있다. run 상태, artifact
계약, orchestrator, Angular store는 앞 단계 계약에 의존하므로 순차 실행한다.

서브에이전트를 사용할 경우 모델은 작업 난이도에 맞게 조정하되 다음을 지킨다.

- 각 에이전트는 하나의 bounded Task만 맡는다.
- 공유 파일을 동시에 수정하지 않는다.
- 구현 에이전트 뒤에 별도 spec/code review를 둔다.
- root agent가 모든 diff와 테스트 결과를 직접 검증한다.
- 현재 작업 트리의 기존 변경을 자신의 변경으로 오인해 삭제하지 않는다.
