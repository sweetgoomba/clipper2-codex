# W07 Storyboard Implementation Plan

> 이 문서는 설계·구현 당시의 결정과 검증 이력을 보존한다. 이후 수정 및 최신 Git/승인 상태는 [스토리보드 작업 카드](../handoff/tasks/storyboard.md)를 우선한다. 9/21 현재 제품 구현은 별도 worktree에 미커밋이며, 사용자는 `.codex` 문서만 커밋·푸시하도록 승인했다.

> 9/21 실행 결과: Task1~8 구현 및 Task9 로컬 검증/인계 완료, 코드·문서 미커밋. 아래는 실행 전 계획 원본이다. 세부 파일명·검증 조합의 실제 결과/판단/미실행 범위는 [최종 기록](2026-09-21-storyboard-implementation-verification.md)을 기준으로 한다. 실제 AI/Build5/운영배포 검증은 제외하며, 체크박스를 일괄 통과 처리하지 않는다.


> **For agentic workers:** Use `superpowers:executing-plans` for direct execution after user review. Tasks use checkbox steps. Do not spawn agents unless the user chooses delegation. No commits or pushes: the user's explicit prohibition overrides skill commit steps.

**Goal:** 승인된 프로필→한 번의 과금 동의→홈 큐→주제/시나리오→대본 중심 상세/PDF 흐름을 실제 저장 데이터와 연결한다.

**Architecture:** Angular는 설정·탐색·동의·진행 표시를 담당한다. 로컬 Nest가 기존 단계별 생성 서비스를 조합해 영속 묶음 작업과 결과를 관리하며, Web API는 추론 계약과 과금/부분 환급의 권위 있는 계산을 담당한다. 기존 v1 결과는 보존하고 새 생성만 명시적 v2 계약을 사용한다. 공통 Jobs/Workflows/Projects/Operations와 다운로드 서비스를 재사용하며 별도 큐·지갑·Electron PDF 런타임을 만들지 않는다.

**Tech Stack:** 기존 Angular/Material/signals, NestJS/TypeScript, 로컬 원자적 JSON 저장, Web API TypeORM/PostgreSQL, Karma/Jasmine·node:test·Jest. PDF는 로컬 Nest PDFKit + 배포된 한글 폰트 사용 제안(새 의존성은 이 기능에 한정).

**Spec:** [UI 합의](2026-09-21-storyboard-ui-design-draft.md), [최종 상세 정정](2026-09-21-storyboard-final-detail-reassessment.md), [분야 목록](2026-09-21-storyboard-category-catalog-draft.md), [목적/스타일](2026-09-21-storyboard-purpose-style-catalog-draft.md), [W07 카드](../handoff/tasks/storyboard.md). 문서의 과거 이력보다 최신 사용자 정정/승인 및 이 계획의 현재 요구사항을 우선한다.

상태: **사용자 승인 후 직접 순차 구현 중**. 9/21 실행 승인. Task 1 계약·호환 읽기 검증을 통과했고 Task 2 프로필 UI/저장 연결을 진행한다. 아래 인터페이스·파일 신설은 구현 제안이며 현재 구현된 API로 오해하지 않는다. 모든 작업을 독립 테스트 가능한 변경 단위로 나누되, 세 저장소가 하나의 사용자 흐름을 공유하므로 통합 순서를 하나의 계획으로 관리한다.

## Global Constraints

- W07은 이번 세션의 선택이며 전체 작업의 영구 우선순위 변경이 아니다.
- 코드·문서 commit/push 금지. 전체 완성/검증 결과를 먼저 보여준 뒤 명시 승인 필요.
- 실제 ML/공급자 호출·Build5·서버 직접 접속·배포 금지. 로컬 mock transport와 임시 저장소로 검증한다. 실제 운영 DB 마이그레이션도 실행하지 않는다.
- 기본 주제 3 × 시나리오 5, 주제 1~5, 시나리오 2~10, 완성 스토리보드당 5크레딧. 기본 75/최소 10/최대 250.
- 프로필 저장은 무료이며 큐를 시작하지 않는다. 수량·가격 동의가 있어야 작업을 시작한다.
- 성공한 중간 결과 보존. 내부 제한 재시도 여부·횟수·중간 파싱 오류를 사용자에게 노출하지 않는다.
- 최종 미완성 수량만 환급한다. 서버 확인 전 환급 완료 표시 금지. 로컬 canned 대체 문서를 성공/과금 대상으로 세지 않는다.
- 프로필/생성 결과 삭제 기능을 새 UI에 제공하지 않는다. 완료 프로필은 복제만 가능, 수정/재생성 금지. 새 프로필은 복제/수정 가능.
- AI 목적/스타일 추천은 보류. 고정 21/128 분야, 분야별 목적 5개, 공통 스타일 24개(8→16→24) 사용.
- 태그 Enter만 추가, 공백 보존, 한글 IME 조합 완료 처리. 목적 직접 입력, 취소 확인, 모달 내부 스크롤 유지.
- 주제 3정보를 신규 생성 응답에서 모두 확보한다. 누락 항목 생략, 왜곡된 기존 필드 대입, 자동 canned 보완 금지.
- 중앙 대본 목록, 상세 3열 유지. 대본·화면 문구·보여줄 화면 및 검색어→AI 영상→AI 이미지 순서. 소재 토글/선정·활용 안내 없음.
- PDF: 프로필/주제/선택 스토리보드 전체 포함, 요약 표→전체 대본 표→구간별 제작 시트. 가변 페이지. 내보내기에 AI 호출/추가 과금 없음.
- 다른 플러그인 리팩터링·미디어 생성·실제 이미지 검색/다운로드·영상 render·목적 추천 AI는 범위 밖이다.

## 현재 실제 상태 (9/21 읽기 전용 확인)

작업 루트: `/Users/jina/project/adlight/.worktrees/storyboard-ux-overhaul-20260920/`

| 약칭 | 저장소 | HEAD | 작업 상태 |
|---|---|---|---|
| A | desktop/clipper_angular | b511e15824eb7ac20d4802e145a6c3a5923f4eb4 | clean |
| N | desktop/clipper_nestjs | c2e227c244e786af4dfa51bd132692eb38cd1cd2 | clean |
| W | web/clipper_web_api | 9304cec77b30b72a9b89355393878a84896dcd86 | clean |

셋 모두 `feature/storyboard-ux-overhaul-20260920`, 로컬 `origin/dev` 대비 ahead/behind 0/0. 이번 확인에서 fetch하지 않았으므로 최신 서버 원격 상태라고 주장하지 않는다. 기존 원본 checkout과 다른 worktree는 보존한다. 세 격리 worktree의 node_modules는 없음. 첫 실행에서 lockfile 기반 준비와 기준선 검증이 필요하다.

확인된 구현 차이:
- `N/.../shortform-director-candidate-generation.service.ts`: `REQUESTED_CANDIDATES_PER_CALL = 20`. 요청 수량 전파와 검증부터 수정해야 한다.
- 기존 research/candidate/production DTO는 단계별 approval을 요구한다. 새 묶음 동의가 내부 단계 호출을 승인하는 범위를 별도 typed context로 전달하며 가짜 approval ID나 confirmed 상수로 우회하지 않는다.
- `N/.../operating-profile.ts`는 domain/targetAudience/objective/toneKeywords/requiredFacts 등의 문자열 기반 v1이다. UI의 선택 구조를 문자열에서 역파싱하면 안 된다. 관련 키워드를 검증된 requiredFacts로 취급하지 않는다.
- `W/.../operations.service.ts`는 succeed 또는 fail 전체 환급, `credit-grants.service.ts`는 원 charge grant별 전액 복원이다. 부분 환급을 UI 계산만으로 구현할 수 없다.
- `N/.../billable-job-attempt.coordinator.ts`의 시작 응답 유실 복구는 실행하지 않고 환급하는 정책이다. 스토리보드 새 실행기가 이 정책과 경쟁해 자동 실행/중복 환급하지 않도록 경계를 둔다.
- `WorkflowExecutor`/registry에 Nest 실행기를 연결할 수 있다. Python 플러그인 런타임으로 스토리보드를 라우팅할 이유가 없다.
- 홈 보관함은 Projects 모델/카드 경로를 사용한다. `core/media-library`는 이미지·음원 소재 저장소이므로 이 결과를 넣지 않는다.
- `A/src/core/download/file-download.service.ts`는 Electron saveUrl과 브라우저 Blob fallback이 이미 있다. 파일 저장창을 새로 만들지 않는다.
- 예시 PDF는 Chromium으로 만든 디자인 산출물이다. 제품에 Chromium/Playwright를 추가한다는 뜻이 아니다.

## Review Focus

1. 시작 응답 유실·더블클릭·재시작: 같은 요청의 중복 차감/작업 생성 금지. Task 5/6 테스트.
2. 부분 결과 수량: research/topic/candidate 어느 단계에서 실패해도 총 요청 슬롯 수를 보존하고 미완성만 환급. Task 3/4/6 테스트.
3. 서로 다른 계정/프로필/작업의 ID 혼용: 결과 조회·정산·PDF 모두 소유권 및 부모 연결 검증. Task 1/5/6/8 테스트.
4. 기존 v1의 다중 컷·새 정보 부재: 원본 삭제/자동 유료 재생성/대본 반복 없이 조회 보존. Task 1/4/7/8 테스트.
5. 긴 한글·영문·태그와 좁은 화면: 잘림 없는 UI/PDF, 조합 중 Enter 오작동 없음. Task 2/7/8 테스트.

## 전부 실패 프로필 정책 — 2026-09-21 사용자 승인

완성 스토리보드가 0개이고 전액 환급이 서버에서 확인되면 같은 프로필의 수정과 새 생성을 허용한다. 환급 확인 전에는 수정·새 생성을 막는다. 일부라도 완성되면 기존 합의대로 프로필을 잠그고 복제만 제공한다.
새 생성은 새로운 수량·과금 동의와 새 batch/operation으로 시작한다. 이전 실패 작업의 기록과 정산 결과는 보존하며, 이전 요청을 재전송해 새 작업을 시작하지 않는다. Task 6/7에서 세 상태와 전환을 함께 검증한다.

다른 기술 제안: 새 프로필의 숨은 기본 길이는 30초로 시작하고 기존 프로필의 저장 길이는 보존한다. 내부 재시도는 논리 단계당 최대 3회(기존 파싱 복구 포함)로 제한하며 실제 provider 호출 수가 상한을 넘지 않도록 통합한다. 이는 과금 단가/사용자 요구의 변경이 아니라 초기 구현 설정이다.

## 파일/인터페이스 경계

아래 경로는 A/N/W 루트 기준이다. `S`는 `src/modules/shortform-director`, `F`는 `src/features/shortform-director`, `I`는 `src/modules/shortform-director-inference`를 뜻한다. 파일별 책임을 명시하며 인접 모듈 전체를 재구성하지 않는다.

### 새 계약 (Task 1에서 정의, 이후 작업이 그대로 사용)

새 타입의 import/export 위치는 위 Create 파일들이다. `deriveBatchCounts`는 UI 기본값 검증 helper이며 실제 과금 금액의 권위는 Task 5의 서버 가격 snapshot이다.

```ts
interface StoryboardProfileSettingsV2 {
  categoryId: string; subcategoryIds: string[]; // 전체는 빈 배열 대신 명시적 all 값
  gender: 'all' | 'male' | 'female'; ageGroups: string[];
  purpose: { kind: 'preset' | 'custom'; value: string };
  styles: string[]; relatedKeywords: string[]; prohibitedKeywords: string[];
}
interface StoryboardBatchRequest {
  profileId: string; topicCount: number; scenariosPerTopic: number;
  clientRequestId: string; quoteId: string;
}
interface StoryboardTopicPlanningV2 {
  recommendationReason: string; audienceQuestion: string; planningPoint: string;
}
interface StoryboardSegmentV2 {
  id: string; order: number; startMs: number; durationMs: number;
  narration: string; onScreenText: string[]; visualDescription: string;
  searchQueries: { ko: string[]; en: string[] };
  aiVideoPromptEn: string; aiImagePromptEn: string; evidenceIds: string[];
}
// OperatingProfileSnapshotV1은 N/S/domain/operating-profile.ts의 기존 타입을 참조한다.
interface StoryboardDocumentV2 {
  schemaVersion: 'shortform-director-storyboard.v2';
  profileSnapshot: OperatingProfileSnapshotV1 & { settingsV2: StoryboardProfileSettingsV2 };
  topicId: string; candidateId: string; title: string; format: string; hook: string;
  topicPlanning: StoryboardTopicPlanningV2;
  segments: StoryboardSegmentV2[];
}
interface StoryboardBatchSummary {
  batchId: string; profileId: string; jobId: string;
  state: 'queued' | 'running' | 'completed' | 'partially_completed' | 'failed';
  requestedCount: number; completedCount: number; failedCount: number;
  settlement: 'pending' | 'confirmed'; chargedCredits: number; refundedCredits: number;
}
```

`profileSnapshot`의 구체적 타입은 `OperatingProfileSnapshotV1 & { settingsV2: StoryboardProfileSettingsV2 }`로 정의한다. 위 계약은 읽기 model에서 명시적으로 버전 분기한다. v2 segment는 TTS 의미/호흡 단위이며 화면을 바꾼다는 이유로 대본을 복제하지 않는다.

REST 제안(N 로컬 API, 기존 인증 컨텍스트 적용):
- `POST /shortform-director/profiles/:profileId/batches/quote` → 서버 가격·수량·프로필 revision에 묶인 quote.
- `POST /shortform-director/profiles/:profileId/batches` → `StoryboardBatchRequest` 검증 후 `{batchId,jobId}`.
- `GET /shortform-director/batches/:batchId` → summary+완성 topic/candidate 결과 참조. 진행중 재시도 정보는 public 응답에 제외.
- `GET /shortform-director/batches/:batchId/storyboards/:candidateId/pdf` → 소유권/부모 검증 후 application/pdf.
- W operation key 제안 `shortform_director.generate`, 단가 5. 다른 operation의 가격/정산 의미 유지.

금액/상태 핵심 규칙:
```ts
const requestedCount = topicCount * scenariosPerTopic;
const refundCount = requestedCount - completedCount;
const refundCredits = refundCount * unitCreditsAtStart;
// 완료는 v2 전체 검증 + 결과 저장 확정 후에만 인정한다.
// 사용자가 보내는 amount/unitCredits/refundCredits는 신뢰하지 않는다.
```

## Task 1: 버전 계약·프로필 snapshot·호환 읽기

**Files**
- Modify N `S/domain/operating-profile.ts`, `operating-profile.input.ts`, `operating-profile.parser.ts`, `storyboard-document.ts`.
- Modify N `S/infrastructure/shortform-director-artifact.registry.ts`, `shortform-director-artifact-json.codec.ts`, `shortform-director-public-artifact.validator.ts`.
- Modify A `F/models/shortform-director-workspace.ts`, `shortform-director-research.ts`, `shortform-director-storyboard.ts`.
- Create N `S/domain/storyboard-batch.ts`, `S/domain/storyboard-v2.ts`, A `F/models/shortform-director-batch.ts`.
- Create N `test/shortform-director-storyboard-v2.test.js`; extend A `F/models/shortform-director-storyboard.spec.ts`.

**Interfaces**: 기존 v1 readers 유지. 위 v2 타입과 `validateStoryboardDocumentV2(value: unknown)` 및 `deriveBatchCounts(topicCount:number, scenariosPerTopic:number)` 공개. v2 validation result는 기존 validator 관례대로 valid/errors를 반환한다.

- [ ] v1 다중 컷 두 개, v2 정상, 필수 검색어/이미지 프롬프트 누락, 타 계정 snapshot, 1×2/5×10/소수/범위 초과 fixture를 추가한다.
- [ ] 아래 경계 테스트를 작성하고 새 validator가 없어 실패함을 확인한다.
```js
assert.deepEqual(deriveBatchCounts(3, 5), { requestedCount: 15, credits: 75 });
assert.throws(() => deriveBatchCounts(6, 5));
assert.throws(() => deriveBatchCounts(3, 2.5));
```
- [ ] v1 원본을 덮어쓰지 않는 union reader/registry 분기를 구현한다. 신규 생성 v2에만 필수 세 정보/소재 계약을 적용한다. v1을 v2라고 표기하지 않는다.
- [ ] 기존 프로필의 domain/audience/objective는 원문 보존. 구조 선택값을 임의 역추정하지 않고 편집 시 기존 값과 재선택 필요 상태를 분리한다. 복제 시 원문 보존을 우선한다.
- [ ] N build 후 대상 node:test, A 관련 모델 테스트 통과 확인. 모듈 외 계약 영향 diff 검토.

## Task 2: 프로필 저장 및 생성/목록 UI

**Files**
- Modify N `S/application/shortform-director-profile.service.ts`, `S/presentation/dto/operating-profile-write-input.mapper.ts`, `create-shortform-director-profile.dto.ts`, `update-shortform-director-profile.dto.ts`, `S/infrastructure/json-shortform-director-profile.repository.ts`.
- Modify A `F/components/operating-profile-form/operating-profile-form.component.{ts,html,scss,spec.ts}`, `operating-profile-array-input.{ts,spec.ts}`; `operating-profile-list/operating-profile-list.component.{ts,html,scss,spec.ts}`; `F/pages/profiles-page/profiles-page.component.{ts,html,scss,spec.ts}`.
- Create A `F/models/storyboard-profile-catalog.ts` (승인 고정 목록, ID/표시명 분리), `storyboard-profile-catalog.spec.ts`.
- Create A `F/components/storyboard-profile-card/storyboard-profile-card.component.{ts,html,scss,spec.ts}` (목록·결과에서 재사용).
- Test N `test/shortform-director-profile-catalog.test.js` 및 기존 profile 테스트들.

**Interfaces**: 입력 settingsV2와 기존 domain/audience/objective를 mapper로 함께 저장; 키워드는 사실(requiredFacts)로 승격하지 않음. 카드 입력은 profile+batch summary, 이벤트는 create/duplicate/edit/openResult.

- [ ] form fixture에 `퇴근 후 시간`을 넣고 Space로 분할되지 않음, 조합중 Enter로 추가되지 않음, Enter 완료 뒤 태그 하나가 추가됨을 테스트한다.
- [ ] 21/128 목록 정확성, 분야별 목적 5개, 스타일 8→16→24, 기존 목적 보존, 빈 필수 생성 비활성, dirty cancel 확인을 먼저 테스트한다.
```ts
expect(catalog.categories.length).toBe(21);
expect(catalog.categories.reduce((n,c)=>n+c.children.length,0)).toBe(128);
```
- [ ] 공통 app-page/Material dialog/confirmation/tokens를 사용해 시안으로 변경한다. 기본 설정과 세부 설정 분리, Enter 태그/×, 높이 제한/내부 스크롤.
- [ ] 완료 카드의 메뉴 복제만/카드 이동, 미생성 카드 수정·복제/카드 무동작을 구현한다. 이름 왼쪽 아이콘 및 삭제 제거. 추천은 빈 화면만.
- [ ] 넓은 카드 한 행·좁은 메타데이터 두 행, 긴 태그 줄바꿈, 메뉴 클릭 버블링 방지·키보드 탐색을 확인한다.
- [ ] 관련 A/N 집중 테스트와 빌드. 완료 잠금의 최종 서버 경합 검증은 Task 6에서 연결한다.

## Task 3: 주제 3정보 및 정확한 후보 수 생성

**Files**
- Modify W `I/domain/shortform-director-inference.contract.ts`, `I/application/shortform-director-inference.prompt.ts`, `shortform-director-inference.input-guard.ts`, `shortform-director-inference.service.ts` 및 각각 spec.
- Modify N `S/application/shortform-director-research.service.ts`, `shortform-director-research-topic.builder.ts`, `shortform-director-candidate-generation.service.ts`, `shortform-director-inference-response.projector.ts`.
- Test N `test/shortform-director-candidate-generation.test.js`, 기존 research 테스트; create `test/shortform-director-batch-counts.test.js`.

**Interfaces**: v2 generation input에 topicCount/scenariosPerTopic/contractVersion 및 internal batch context 전달. 기존 API의 v1 default는 유지. v2는 요청한 수량 및 세 topic 정보 검증.

- [ ] 요청 4×4가 research 4개·각 후보 4개로 전달되고 기존 상수 20이 적용되지 않는 spy 테스트를 먼저 추가한다.
- [ ] 주제 정보 누락/공백/서로 중복, 후보 중복 ID/부족/초과, 상한 5×10을 fixture로 검사한다.
- [ ] topic-synthesis 기존 호출에서 추천 이유/궁금증/기획 포인트를 함께 생성한다. 짧은 한 문장/구를 요구하며 whyNow/audienceSignal을 의미 검증 없이 대입하지 않는다.
- [ ] v2 요청 count를 프롬프트/응답 검증/저장까지 전파한다. 초과 반환을 UI에서만 자르거나 성공 count로 속이지 않는다. 유효 항목은 저장하고 부족 슬롯을 별도로 기록한다.
- [ ] 수량 실패를 Task 6의 슬롯 계산에 전달한다. 주제 하나 실패하면 그 아래 요청된 시나리오 슬롯도 미완성으로 남긴다.
- [ ] W Jest prompt/contract/input/service 집중 테스트, N build+관련 node:test. 실제 transport는 test double만.

## Task 4: 대본 중심 v2 제작·품질 검증·내부 복구

**Files**
- Modify W Task 3 contract/prompt/service 및 `I/infrastructure/openai-shortform-director-inference.transport.spec.ts`, Google transport spec.
- Modify N `S/application/shortform-director-candidate-production.service.ts`, `shortform-director-storyboard.assembler.ts`, `shortform-director-storyboard.validator.ts`.
- Create N `S/application/storyboard-batch-stage-adapter.ts`, `S/application/storyboard-stage-retry.ts`.
- Test N `test/shortform-director-candidate-production.test.js`, create `test/storyboard-stage-retry.test.js`; A storyboards model spec.

**Interfaces**: `runStageWithRetry<T>(execute:(attempt:number)=>Promise<T>, options:{maxAttempts:number; signal:AbortSignal; isRetryable:(error:unknown)=>boolean}):Promise<T>`. Adapter exposes research/candidates/editorial/material stage completion promises backed by existing run artifacts, not UI polling state.

- [ ] stage returns invalid JSON once then valid → 2 calls, parent stages not called again. editorial succeeds, material fails → editorial artifact reused. All attempts fail → no canned success.
```js
let attempts = 0;
await assert.rejects(runStageWithRetry(async () => { attempts++; throw new Error('parse'); }, {
  maxAttempts: 3, signal: new AbortController().signal, isRetryable: () => true,
}));
assert.equal(attempts, 3);
```
- [ ] 401/403/잘못된 입력/취소는 재시도하지 않는다. 429/일시적 5xx/timeout/응답 파싱·검증 실패만 상한 안에서 재시도한다. 기존 repair를 포함해 실제 공급자 호출 총 3회 상한을 지킨다.
- [ ] editorial 대본→material 생성 의존 관계를 유지하고 TTS 구간마다 visualDescription/searchQueries/AI 영상·이미지 프롬프트를 생성한다. 사용자용 장면/컷 이중 계층을 새로 만들지 않는다.
- [ ] 검색어는 대상/행동/필요한 고유명사를 짧게 제시하며 영상/사진 접미사를 일괄 추가하지 않는다. 이미지 프롬프트는 정지 상태를 설명하고 영상 프롬프트의 길이는 구간에 맞춘다. 소재 설명은 직접 촬영을 전제하지 않는다.
- [ ] 작업을 막지 않는 품질 경고와 계약 불성립을 분리한다. 필수 소재/대본/시간 정합성 누락을 경고로 낮춰 성공 처리하지 않는다. evidence 연결은 저장하고 원시 ID를 주 화면에 노출하지 않는다.
- [ ] v1 다중 shot은 읽기 시 모든 정보를 보존한다. 새 정보가 없는 경우 이전 형식임을 표시하며 가짜 값/무단 AI 보완을 하지 않는다. 이전 형식 호환을 이유로 신규 v2의 필수 항목을 생략하지 않는다.
- [ ] 관련 N/W 집중 테스트와 빌드를 실행한다. public summary에 retry/repair/provider 진단 정보가 섞이지 않는 계약 테스트를 추가한다.

## Task 5: 수량 과금·부분 환급과 영속 정산

**Files**
- Modify W `src/modules/operations/domain/operation-definitions.ts`, `operations.repository.ts`, `application/operations.service.ts`, `operation-policy-seeder.ts`, `presentation/operations.controller.ts`, `infrastructure/typeorm-operations.repository.ts`, `operation-run.entity.ts` 및 대응 spec.
- Modify W `src/modules/credits/application/credit-grants.service.ts`, `domain/credits.repository.ts`, `infrastructure/typeorm-credits.repository.ts` 및 대응 spec.
- Create W `src/modules/operations/presentation/dto/settle-storyboard-operation.dto.ts`, `application/storyboard-settlement.ts`, `application/storyboard-settlement.spec.ts`.
- Create W `src/modules/operations/infrastructure/storyboard-completion-receipt.entity.ts`, `application/storyboard-completion-receipt.service.ts` 및 대응 spec. receipt는 operationRunId/slotId/candidateId/editorialHash/materialHash/validationVersion을 저장하고 `(operationRunId, slotId)`를 unique로 둔다. v2 추론에서 서버가 검증한 결과만 receipt로 등록한다.
- Create W user migration `src/core/database/migrations/user/1790000000000-AddStoryboardOperationSettlement.ts` (프로젝트 실제 migration ordering 확인 후 충돌 없이 번호 선택; 운영 실행 금지).
- Modify N `src/core/web-api/web-api-operation-run.service.ts`, `src/modules/operations/domain/billable-job-attempt.ts`, `application/billable-job-attempt.coordinator.ts`, `billing-terminal-finalizer.ts`, `billing-terminal-outbox.service.ts` 및 기존 billing tests.

**Interfaces**: quote/start에 requestedStoryboardCount를 별도 필드로 추가(기존 generatedVideoCount 의미 오염 금지). 시작시 unit price/quantity/quote revision을 server snapshot으로 보존. 신규 settle은 batchId/requestedCount/completed candidate references를 검증하고 서버 저장 단가로 계산. settle 입력의 직접 refund amount는 금지.

- [ ] 3×5=75, 12완료/3실패=15환급, 0완료=75환급, 재전송=동일 결과를 먼저 테스트한다. 기본 policy seed 5, 기존 관리 단가를 매번 덮어쓰지 않는다.
- [ ] 여러 credit grants에서 차감한 경우 일부 금액만 원 grants로 돌려주고 charge 이상 환급 금지. 만료/revoked/refund_locked 원장 상태 규칙 유지. 동일 operation settlement 재실행은 원장 추가 0건.
- [ ] 기존 operation status는 유지한다. 성공 1개 이상이면 `succeeded`+정산 수량/환급액, 0개면 `failed`+전액 환급이다. UI의 partially_completed는 batch summary에서 파생한다. Task 5에서 추가한 nullable 수량/단가/정산완료 필드는 구 operation의 읽기를 깨지 않는다.
- [ ] operation row lock→계정 grant lock→환급 ledger→완료 수량/환급액 기록을 동일 transaction으로 묶는다. 과거 full-refund 경로의 동작은 변경하지 않는다.
- [ ] requestedCount를 start snapshot과 비교, completedCount는 고유 slot/candidate 완료 evidence와 범위 검증. desktop 진술만으로 미확인 성공을 확정하지 않도록 v2 inference 완료 receipt/연결을 검증한다. 과금 operation 소유권을 새 v2 inference 진입에도 연결한다.
- [ ] 진행중 UI 합계/금액은 server quote 표시. stale quote는 다시 동의받으며 UI 값을 믿고 진행하지 않는다. 한 요청 재전송은 같은 clientRequestId/clientAttemptKey 사용.
- [ ] terminal outbox에 settlement intent/quantity/evidence를 저장 후 송신. 네트워크 실패는 pending, server 응답 확인 뒤 confirmed. 기존 fail/succeed 이벤트로 부분 성공을 전액 환급하지 않도록 분기한다.
- [ ] 테스트 예: 75차감 후 settle(12) 두 번 → balance 변화 -60, refund ledger 합계15, completedCount12 불변. 동일키 다른 payload는409. 다른계정404/403.
- [ ] W operations/credits/recovery Jest, N billing crash/restart/outbox node:test와 build. 로컬 격리 PostgreSQL transaction 검증을 실행 단계에 포함하며 환경 미제공이면 미실행을 명시하고 완료 판정 보류. 운영DB 접속 금지.

## Task 6: 영속 묶음 작업·홈 큐·결과 보관

**Files**
- Create N `S/domain/storyboard-batch.repository.ts`, `S/infrastructure/json-storyboard-batch.repository.ts`, `S/application/storyboard-batch.service.ts`, `storyboard-batch.executor.ts`, `storyboard-batch-recovery.service.ts`, `S/presentation/storyboard-batch.controller.ts`, `S/presentation/dto/start-storyboard-batch.dto.ts`.
- Modify N `src/modules/shortform-director/shortform-director.module.ts`; `src/modules/workflows/application/workflow-executor-registry.service.ts`와 module provider registration; `src/modules/jobs/application/jobs.service.ts`; `src/modules/projects/domain/project.model.ts`, `src/modules/projects/application/projects.service.ts`, `project-detail-builder.ts`.
- Test create N `test/storyboard-batch-executor.test.js`, `storyboard-batch-recovery.test.js`, `storyboard-batch-controller.test.js`; extend billing-restart/crash tests.

**Interfaces**: `StoryboardBatchExecutor` implements existing `WorkflowExecutor` with pluginName `shortform_director`. 로컬 batch는 요청 slot, immutable profile snapshot, research/candidate/editorial/material artifact refs, per-stage attempts, billing attempt ID, settlement state를 저장한다. auth token/API key는 JSON에 저장하지 않는다.

- [ ] 한 profile 중복 start 경쟁, start 응답 유실, snapshot 저장 실패, 연구 성공 뒤 재시작, material 저장 직후 종료, 정산 응답 유실을 재현하는 테스트부터 작성.
- [ ] profile별 atomic lock/unique active batch와 clientRequestId를 먼저 저장한다. 과금 전 preflight로 입력·권한·공급자 설정·저장 가능 여부를 확인한다. 과금 거절이면 생성 실행하지 않는다.
- [ ] 전체 consent를 내부 stage adapter의 typed batch approval로 전달한다. UI의 개별 단계 승인창은 새 흐름에서 열지 않는다. 기존 v1 endpoint 보호를 약화시키지 않는다.
- [ ] 주제 생성 후 각 주제 후보 생성, 각 후보 editorial→material 생성. 초기에는 stage 동시성2 이하로 제한하고 부모 완료 의존만 지키며 불필요한 전체 barrier를 강제하지 않는다.
- [ ] 성공 checkpoint는 결과 저장 확정 뒤 갱신. 중단 후 완료된 stage를 다시 호출하지 않는다. 성공 여부 불명인 미완료 provider 요청은 재호출 비용 가능성이 있으므로 외부 API exactly-once를 약속하지 않는다. 사용자 과금은 동일 operation으로 유지한다.
- [ ] 15슬롯 중3미완성, 후보부족, 주제부족 모두 requestedCount=15를 유지. duplicate 후보를 다른슬롯 성공으로 중복 계산하지 않는다. 완성12개는 즉시 조회 가능하되 정산 pending 동안 환급 완료로 표시하지 않는다.
- [ ] 시작 응답이 유실돼 기존 coordinator가 환급한 abandoned attempt는 실행하지 않는다. running 상태에서 중단된 batch만 동일 operation/신선한 로그인 토큰으로 복구한다. 미로그인 대기 중 무조건 fail/refund하지 않는다.
- [ ] 미실행 queue 취소는 전액 환급, 실행중 취소는 저장 완료된 결과 기준 정산. 일반 retry 버튼으로 새과금/새batch를 만드는 경로는 이 플러그인에서 비활성화한다. 전부 실패 후 환급 confirmed일 때만 프로필 수정/새 시작을 허용한다. 새 시작은 새 quote·동의·batch·operation을 사용하고 이전 실패 이력을 보존한다.
- [ ] Jobs executor 완료 전에 manifest commit. Projects에는 metadata 기반 storyboard 결과 카드와 batch 참조를 저장한다. 영상파일 없는 결과도 목록에 남고 잘못된 영상 플레이어를 열지 않는다.
- [ ] 0완료+정산 pending은 수정/새 시작 거부, 0완료+정산 confirmed는 허용, 1개 이상 완료는 거부하는 backend 테스트를 작성한다. 새 생성의 동시 요청은 하나의 새 batch만 만들고 이전 operation을 재사용하지 않음을 검증한다.
- [ ] 기존 완료 프로필 update도 backend에서409. 복제는 설정만 새ID로 저장하고 batch/과금/결과를 복사하지 않는다.
- [ ] focused node:test + build; 임시파일 저장소로2회재시작해 복구멱등성 검증.

## Task 7: 새 Angular 흐름·큐·상세 연결

**Files**
- Create A `F/services/shortform-director-batch.service.ts`, `shortform-director-batch.gateway.ts`, `F/state/shortform-director-batch.store.ts` 및 대응 spec.
- Create A `F/components/storyboard-generation-dialog/storyboard-generation-dialog.component.{ts,html,scss,spec.ts}`.
- Modify A `F/pages/{profiles-page,ideas-page,production-page}`의 component ts/html/scss/spec; `F/layout/shortform-director-shell/` 및 routing guards/integration spec; `src/app/app.routes.ts`.
- Modify A `F/components/storyboard-scene-list/`, `F/services/storyboard-clipboard.service.{ts,spec.ts}`; 기존 quality/evidence 컴포넌트는 사용자용 근거 탐색에 재사용.
- Modify A `src/shell/projects/projects-queue/projects-queue.component.*`, `models/queue-view.ts`, `models/project-card.builder.ts`, `project-card/project-card.component.*`, `projects-detail-page/projects-detail-page.component.*` 및 대응 spec.
- Modify A `src/core/navigation/page-guide-content.ts`.

**Interfaces**: HTTP batch summary→store→public UI. retry 내부 field에 FE 의존 금지. 결과 route는 profileId/batchId/candidateId 연결 검증, 완료시프로필카드재사용.

- [ ] profile save가 quote/start를 호출하지 않음, modal cancel이차감없음, 4×4=80표시, 더블클릭start1회, stale quote재확인, credit부족, 환급pending→confirmed 표시 전환을 테스트한다.
- [ ] 전부 실패 상태에서 환급 pending 동안 수정/생성 버튼이 비활성이고 confirmed 후 활성화되는지, 일부 완료는 복제만 가능한지 테스트한다. 새 생성에는 다시 수량·과금 동의가 필요하고 이전 실패 이력은 남는지 확인한다.
- [ ] 최초 4단계 안내/두버튼, 생성 dialog server quote연결, 홈 큐 이동, completed/partial result 카드 연결을 구현한다. 다른플러그인 queue표시회귀 금지.
- [ ] 결과 상단 뒤로가기+전체프로필카드, 주제별 시나리오 가로한줄(타입·제목·훅), 카드클릭 상세. 새로고침/deeplink/뒤로가기에서 선택한 batch/주제를 복원한다.
- [ ] 상세3열 고정+내부가로스크롤, 중앙TTS전문, 오른쪽대본/화면문구/보여줄화면/검색어/두프롬프트. 가격·모델·evidenceID·retry로그 제거. 자료선택토글없음.
- [ ] 전체대본복사 순서/공백 보존, 개별검색어·영상/이미지프롬프트 정확한복사, 선택변경 후 stale내용없음 테스트.
- [ ] legacy v1은 원본문맥과다중컷정보를읽기전용으로유지하고 새필드 부재는 이전형식 표시. 신규v2 누락시빈UI성공금지.
- [ ] Angular집중단위테스트/스타일검증/build. 1920/1280/768/390 라이트·다크 시각검증, 모달키보드·focus·scroll 유지 확인.

## Task 8: 실제 PDF 생성·다운로드

**Files**
- Create N `S/application/storyboard-export.model.ts`, `storyboard-pdf.service.ts`, `S/infrastructure/storyboard-pdf.renderer.ts`, `S/presentation/storyboard-export.controller.ts`.
- Modify N module 등록, `package.json`/`package-lock.json`(PDFKit 및 타입만), `scripts/copy-assets.mjs`(필요 시 한글 폰트 배포 경로 보강).
- Create N `test/storyboard-pdf.test.js`, `test/storyboard-export-controller.test.js`.
- Create A `F/services/storyboard-export.service.ts` 및 spec; production page의 버튼에 연결. Reuse `src/core/download/file-download.service.ts`.

**Interfaces**: `createStoryboardExportModel(profileSnapshot, topic, document)`은 immutable 저장값에서 문서모델 생성. `StoryboardPdfService.render(model): Promise<Buffer>`는 AI/HTTP호출없음. owner-bound PDF endpoint→FileDownloadService.save(url,filename). 기존 로컬 다운로드 인증 패턴을 확인해 재사용하고 토큰을 querystring에 노출하지 않는다.

- [ ] 현재선택구간5에서도 전체구간1~5포함, 프로필/주제교차ID차단, API/AIcall0, 긴한글/영문/특수문자/금지키워드없음 및 다중페이지를 테스트한다.
- [ ] PDFKit을 선택해 문서 렌더러에만 의존시키고 패키지/lock 함께 저장. 기존 배포한글폰트 경로로 폰트등록/임베딩. macOS시스템폰트/개발자경로에의존하지 않는다.
- [ ] 요약표→대본표→구간별제작시트 구조 구현. 긴프롬프트는 단어/행 기준 다음페이지로이어짐, 표제목/구간번호반복, 푸터겹침금지. 페이지수7고정금지.
- [ ] 저장파일명은 프로필/제목과안전한구분자로생성하며 경로문자제거. Content-Type/Disposition 적용. 취소는오류/완료알림없음, 실패는재다운로드가능하고 생성재실행안함.
- [ ] 기존 v1export는 있는 원본만 과거형식임을표시하며 새프롬프트를 꾸며내지 않는다.
- [ ] PDF텍스트추출로모든필드확인, Poppler렌더로모든페이지확인. 짧은예시·긴프로필·긴대본·긴프롬프트/한글모음 fixture 검증. A download/cancel spec 및 N build/node:test.

## Task 9: 전체 검증·인계

- [ ] 의존성준비: 각worktree에서 `npm ci`(lock기준,원본node_modules복사/공유수정금지). 이번계획단계에서는실행하지않음.
- [ ] 기준선: A `npx ng test --watch=false --browsers=ChromeHeadless --include='src/features/shortform-director/**/*.spec.ts'`; N `npm run build` 후 `node --test test/shortform-director*.test.js`; W `npm test -- --runInBand shortform-director-inference`. 기준선실패는수정회귀와구분.
- [ ] 변경후집중검증:
```sh
# A
npx ng test --watch=false --browsers=ChromeHeadless --include='src/features/shortform-director/**/*.spec.ts' --include='src/shell/projects/**/*.spec.ts' --include='src/core/download/*.spec.ts'
npm run test:styles
npm run build
# N (node:test가 dist를 읽으므로 build 먼저 실행)
npm run build
node --test test/shortform-director*.test.js test/storyboard*.test.js test/billing-*.test.js test/billable-job-attempt-coordinator.test.js
# W
npm test -- --runInBand shortform-director-inference operations credits
npm run build
```
- [ ] 가짜 provider + 로컬 임시 저장 + 테스트용 과금 adapter로 3×5, 1×2, 5×10, 전부 실패, 부분 실패, 실패 뒤 복구를 end-to-end 확인한다. 실제 ML 실행 없음.
- [ ] 마이그레이션은 로컬 격리 DB에서 up/down/재실행, 다른 operation 회귀, 동시 settle 경쟁을 확인한다. 미실행이면 완료로 처리하지 않는다.
- [ ] 신규/기존 저장 fixture, 소유자 혼용, 재시작/응답 유실, PDF 전체 페이지, UI 각 너비, 복사 값을 확인한다.
- [ ] 전체 diff에서 불필요한 리팩터링/비밀값 혼입을 자체 검토한다. mock 성공만으로 실제 생성 품질을 검증했다고 주장하지 않는다.
- [ ] 실제 ML 미실행 제약을 검증 결과에 명시한다. 필요한 실생성 수용 검증은 별도 사용자 승인으로 진행한다.
- [ ] W07 카드·WORKBOARD의 W07 행·당일 세션·구현/검증 기록을 갱신한다. commit/push 없이 변경 파일 목록·테스트 결과·남는 제약을 제출한다.

## 완료 기준

프로필 저장→동의→큐→완성 결과 탐색→PDF 저장이 mock backend/provided test fixtures 기반으로 연결되고, 성공 결과 보존/재시작/정산 멱등성/부분 환급이 테스트로 검증되어야 한다. 실제 AI 결과 품질은 별도 승인된 실행 없이는 검증 완료로 쓰지 않는다. 불완전 v2결과를 성공 처리하거나 문서에서 필수 정보를 숨겨 완료로 만들지 않는다.

## 계획 검토와 진행

구현 방식 권장: 이 세션에서 직접 순차 구현. 계약·정산·실행기가 서로 결합돼 있어 동일 맥락을 유지하면서 Task별 테스트를 통과시키는 편이 적합하다. 0개 완료 프로필 재사용 정책은 승인됐다. 사용자가 계획대로 이 세션에서 직접 순차 구현하는 방식에 동의했다. Task별 검증과 기록을 남기며 계속 진행한다. 문서의 스킬 기본 commit지시는 적용하지 않는다.


## PDF 구현 근거

9/21 공식 문서에서 Node PDFKit의 폰트 임베딩, 자동 줄바꿈/페이지 흐름, 표 지원을 확인했다. 이것이 실제 프로젝트의 한글/긴 문서 테스트를 대체하지 않는다. 설치 버전은 실행 시 기존 Node/번들 호환성을 확인해 lockfile에 고정한다.
- [텍스트와 폰트](https://pdfkit.org/docs/text.html)
- [표](https://pdfkit.org/docs/table.html)
