# Shortform Director Candidate Evidence ID Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 후보 생성 모델이 내부 artifact ID 대신 허용된 source ID를 사용하고, 검증 실패 재시도에서 같은 오류를 반복하지 않게 한다.

**Architecture:** 로컬 grounded context는 lineage 정본으로 유지하고, provider envelope에는 내부 lineage 필드를 제거한 projection을 넣는다. Candidate prompt v3가 출력 ID 매핑을 명시하며, Desktop은 검증 결과에서 만든 bounded correction을 다음 호출에 전달한다.

**Tech Stack:** NestJS 11/Jest(Web API), NestJS 10/TypeScript/node:test(Desktop), 로컬 JSON lineage artifact

## Global Constraints

- 사용자 앱 패키징 빌드는 실행하지 않는다.
- 유료 provider E2E 호출은 실행하지 않는다.
- 기존 dirty worktree의 관련 없는 변경은 수정하거나 되돌리지 않는다.
- candidate-generation-input에는 로컬 lineage ID를 보존한다.
- provider-facing candidate envelope에서는 내부 artifact/run ID를 제거한다.
- 현재 prompt는 v3이며 저장된 v1·v2 계약은 읽기 호환한다.

---

### Task 1: Web API candidate prompt v3

**Files:**
- Modify: `web/clipper_web_api/src/modules/shortform-director-inference/application/shortform-director-inference.prompt.spec.ts`
- Modify: `web/clipper_web_api/src/modules/shortform-director-inference/application/shortform-director-inference.service.spec.ts`
- Modify: `web/clipper_web_api/src/modules/shortform-director-inference/application/shortform-director-inference.prompt.ts`

**Interfaces:**
- Consumes: candidate inference envelope의 `groundedContext`와 선택적 `correction`
- Produces: `shortform-director.candidate-generation.v3` provider input contract

- [x] **Step 1: Write the failing prompt contract tests**

  `candidate-generation` spec가 v3인지, `evidenceIds`가
  `marketEvidence[].sourceItemId`만 사용해야 하는지, artifact/run ID를
  금지하는지, correction을 따라야 하는지 검증한다.

- [x] **Step 2: Run the focused Jest tests and verify RED**

  Run:
  `npm test -- --runInBand src/modules/shortform-director-inference/application/shortform-director-inference.prompt.spec.ts src/modules/shortform-director-inference/application/shortform-director-inference.service.spec.ts`

  Expected: v2 또는 누락된 ID 매핑 문구 때문에 FAIL.

- [x] **Step 3: Implement the v3 prompt**

  `spec()`의 candidate version을 v3로 올리고 정확한 세 ID 배열의 입력 필드
  매핑, 내부 lineage ID 금지, correction 준수를 system prompt에 추가한다.

- [x] **Step 4: Re-run the focused Jest tests**

  Expected: PASS.

### Task 2: Desktop provider context projection and correction envelope

**Files:**
- Modify: `desktop/clipper_nestjs/test/shortform-director-candidate-generation.test.js`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-candidate-generation.service.ts`

**Interfaces:**
- Consumes: `PreparedGroundedCandidateGenerationContext`,
  `ShortformDirectorCandidateValidationIssue[]`
- Produces: provider-facing grounded context without internal lineage and
  `shortform-director-candidate-correction.v1`

- [x] **Step 1: Write the failing integration test**

  실제 candidate service harness에서 첫 응답은 `artifact.director.*`를
  evidence ID로 반환하게 한다. 첫 provider request의 grounded context에는
  `artifactId`와 `normalizationArtifactId`가 없고, 로컬
  `candidate-generation-input.groundedContext`에는 둘 다 있어야 한다.
  두 번째 request에는 `unknown-evidence`와 허용 `sourceItemId` 목록이 들어가야
  하며, 해당 source ID를 사용한 두 번째 응답으로 실행이 성공해야 한다.

- [x] **Step 2: Build and run the focused node:test file to verify RED**

  Run:
  `npm run build && node --test test/shortform-director-candidate-generation.test.js`

  Expected: provider input에 내부 lineage가 남아 있거나 correction이 없어서 FAIL.

- [x] **Step 3: Add the provider projection**

  `candidateInferenceEnvelopeFromParts()`가 전체 local context 대신 내부 lineage
  필드를 제외한 새 객체를 사용하도록 한다. `publishInput()`의
  `groundedContext`는 기존 원본을 유지하고 `baseEnvelope`는 실제 provider
  projection을 보존한다.

- [x] **Step 4: Add bounded correction**

  첫 attempt에는 `correction: null`을 넣는다. validation의 고유 issue 목록과
  grounded context에서 얻은 세 허용 ID 목록으로 다음 attempt correction을 만든다.
  최대 preflight envelope에는 모든 validation issue가 포함된 최대 correction을
  사용한다.

- [x] **Step 5: Rebuild and run the focused node:test file**

  Expected: PASS.

### Task 3: Desktop prompt contract compatibility

**Files:**
- Modify: `desktop/clipper_nestjs/test/shortform-director-web-api-clients.test.js`
- Modify: `desktop/clipper_nestjs/test/shortform-director-reference-analysis-cost.test.js`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-source-fetch-response.projector.ts`
- Modify: `desktop/clipper_nestjs/test/shortform-director-candidate-generation.test.js`

**Interfaces:**
- Consumes: Web API runtime status candidate prompt version
- Produces: current v3 contract with persisted v1·v2 compatibility

- [x] **Step 1: Update tests to expect v3 and explicitly cover v1/v2 compatibility**

  Runtime fixtures and inference audit fixtures use v3. A table-driven projector test
  supplies v1 and v2 and verifies both survive exact projection.

- [x] **Step 2: Build and run affected tests to verify RED**

  Run:
  `npm run build && node --test test/shortform-director-candidate-generation.test.js test/shortform-director-web-api-clients.test.js test/shortform-director-reference-analysis-cost.test.js`

  Expected: projector allowlist가 v3를 거절해 FAIL.

- [x] **Step 3: Add v3 to the exact projector allowlist**

  `ShortformDirectorCandidateProviderInputContract.promptTemplateVersion`
  union과 parser에 v3를 추가한다. v1·v2는 제거하지 않는다.

- [x] **Step 4: Rebuild and run affected tests**

  Expected: PASS.

### Task 4: Final verification and design status

**Files:**
- Modify: `.codex/design/2026-08-06-shortform-director-candidate-evidence-id-repair-design.md`

**Interfaces:**
- Consumes: Task 1–3 test results
- Produces: verified implementation record

- [x] **Step 1: Run Web API focused verification**

  Run:
  `npm test -- --runInBand src/modules/shortform-director-inference/application/shortform-director-inference.prompt.spec.ts src/modules/shortform-director-inference/application/shortform-director-inference.service.spec.ts`

  Run: `npm run build`

- [x] **Step 2: Run Desktop focused verification**

  Run:
  `npm run build`

  Run:
  `node --test test/shortform-director-candidate-generation.test.js test/shortform-director-web-api-clients.test.js test/shortform-director-reference-analysis-cost.test.js`

- [x] **Step 3: Mark the design implemented with exact verification results**

  검증 명령, 통과한 test 수, 실행하지 않은 유료 E2E와 사용자 앱 빌드를 기록한다.
