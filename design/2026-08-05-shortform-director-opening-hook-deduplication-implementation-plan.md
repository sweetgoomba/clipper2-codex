# Shortform Director Opening Hook Deduplication Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use `superpowers:test-driven-development` to implement this plan task by task and `superpowers:verification-before-completion` before reporting success.

**Goal:** 새로 생성하거나 재생성한 스토리보드의 첫 장면에서 선택 후보의 훅을 내레이션과 primary text에 각각 정확히 한 번만 사용한다.

**Architecture:** Web API prompt는 LLM에게 첫 장면 훅의 exact-copy/no-restatement 계약을 전달한다. Desktop compiler는 LLM 출력과 무관하게 첫 narration cue와 첫 primary text layer를 `candidate.hook`으로 결정해 최종 불변식을 보장한다. 두 번째 장면 이후와 CTA 처리는 유지한다.

**Tech Stack:** NestJS, TypeScript, Jest, Node.js built-in test runner

**Constraints:** 기존 저장 artifact와 프로젝트는 마이그레이션하지 않는다. 유료 공급자를 호출하지 않는다. Electron 앱 패키징을 실행하지 않는다. 사용자가 요청하기 전에는 커밋하거나 푸시하지 않는다.

---

## Task 1: Lock the Web API video-plan prompt contract

**Files:**

- Modify: `web/clipper_web_api/src/modules/shortform-director-inference/application/shortform-director-inference.prompt.spec.ts`
- Modify: `web/clipper_web_api/src/modules/shortform-director-inference/application/shortform-director-inference.prompt.ts`

### Step 1: Write the failing prompt-contract test

- `video-plan` prompt version이 `shortform-director.video-plan.v4`인지 검증한다.
- prompt가 `scenes[0].narration`을 입력 `candidate.hook`과 정확히 같게 만들도록 명시하는지 검증한다.
- 훅을 한 번만 사용하고 바로 뒤에서 바꿔 말하거나 다시 진술하지 않도록 명시하는지 검증한다.

### Step 2: Run the focused test and confirm RED

Run:

```bash
npm test -- --runInBand src/modules/shortform-director-inference/application/shortform-director-inference.prompt.spec.ts
```

Expected: 기존 v3 및 누락된 exact-hook 지시 때문에 실패한다.

### Step 3: Implement the minimal prompt change

- `video-plan` prompt template version을 v4로 올린다.
- 첫 장면 narration exact-copy/no-restatement 지시만 추가한다.
- 기존 TTS, audio policy, shot-duration 지시는 보존한다.

### Step 4: Re-run the focused test and confirm GREEN

Run the same focused Jest command.

Expected: PASS.

## Task 2: Enforce the opening-hook invariant in the Desktop compiler

**Files:**

- Modify: `desktop/clipper_nestjs/test/shortform-director-candidate-production.test.js`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-candidate-plan.compiler.ts`

### Step 1: Write regression tests from the observed artifacts

Compiler test에 다음 두 실제 실패 유형을 입력한다.

- 문장부호만 다른 첫 장면 narration
- 의미는 같지만 표현이 다른 첫 장면 narration

각 입력에 대해 다음을 검증한다.

- 첫 narration cue는 `candidate.hook`과 정확히 같다.
- 첫 primary text layer는 `candidate.hook`과 정확히 같다.
- 두 번째 장면 narration은 LLM 입력을 그대로 유지한다.

### Step 2: Build and run the focused test to confirm RED

Run:

```bash
npm run build
node --test test/shortform-director-candidate-production.test.js
```

Expected: 기존 `includeRequiredCopy`가 후보 훅과 LLM 표현을 이어 붙여 새 회귀 테스트가 실패한다.

### Step 3: Implement the minimal compiler invariant

- 첫 장면 narration을 `candidate.hook.trim()`으로 결정한다.
- 첫 장면 primary text도 `candidate.hook.trim()`으로 결정한다.
- 첫 장면 이후 narration과 CTA required-copy 경로는 변경하지 않는다.
- fuzzy/semantic 비교 로직은 추가하지 않는다.

### Step 4: Rebuild and re-run the focused test

Run the same build and Node test commands.

Expected: PASS.

## Task 3: Verify affected boundaries

**Files:**

- Verify only; no planned source changes

### Step 1: Verify the Web API

Run:

```bash
npm test -- --runInBand src/modules/shortform-director-inference/application/shortform-director-inference.prompt.spec.ts
npm run build
```

### Step 2: Verify the Desktop Shortform Director boundary

Run:

```bash
npm run build
node --test test/shortform-director-candidate-production.test.js test/shortform-director-storyboard-only-boundary.test.js
```

### Step 3: Inspect the final scoped diff

Run `git diff --check` and inspect only the four implementation/test files plus the two design/plan documents.

Expected:

- No whitespace errors.
- No schema or HTTP API changes.
- No app packaging.
- No paid provider calls.
- Existing stored storyboards remain unchanged; new or regenerated storyboards use the corrected opening hook.
