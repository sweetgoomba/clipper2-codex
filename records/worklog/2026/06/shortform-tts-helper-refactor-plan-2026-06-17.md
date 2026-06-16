# Shortform TTS Helper Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move full-project TTS regeneration and server/local project merge helpers out of `ShortformWorkflowPageComponent` while preserving shortform preview, template, and caption regeneration behavior.

**Architecture:** Add `src/features/shortform/pages/shortform-workflow-tts.ts` as a page-adjacent helper module. The helper owns pure project transforms and the async regeneration loop; the Angular page continues to own signals, overlay labels, error handling, and preview reset.

**Tech Stack:** TypeScript pure helpers, Angular service interface by structural typing, Jasmine/Karma for helper and page regression tests.

---

### Task 1: TTS Helper Contract Tests

**Files:**
- Create: `src/features/shortform/pages/shortform-workflow-tts.spec.ts`

- [x] **Step 1: Write failing tests**

Add tests for:
- `withLocalNarrationText` preserves local edited text on the latest server project.
- `withLocalClipOrder` reorders server clips according to local clip order.
- `regenerateShortformProjectTts` synthesizes lines in local order, applies selected TTS settings, and accumulates duration updates from per-line server responses.

- [x] **Step 2: Run tests to verify RED**

Run:
```bash
./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless '--include=src/features/shortform/pages/shortform-workflow-tts.spec.ts'
```

Expected: FAIL because the helper module does not exist yet.

### Task 2: Extract Helper Logic

**Files:**
- Create: `src/features/shortform/pages/shortform-workflow-tts.ts`
- Modify: `src/features/shortform/pages/shortform-workflow-page.component.ts`

- [x] **Step 1: Implement helper module**

Move the selected TTS settings, local narration text, local clip order, merged server update, narration duration, and full-project TTS regeneration logic into exported functions.

- [x] **Step 2: Delegate page methods**

Replace page-private helper bodies with imports. Keep `regenerateProjectTts` on the page as a thin signal/error wrapper around `regenerateShortformProjectTts`.

- [x] **Step 3: Run targeted tests**

Run:
```bash
./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless '--include=src/features/shortform/pages/shortform-workflow-tts.spec.ts'
./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless '--include=src/features/shortform/pages/shortform-workflow-page.component.spec.ts'
```

Expected: PASS.

### Task 3: Verify Refactor Safety

**Files:**
- Modify only if verification reveals a regression in files changed by Task 2.

- [x] **Step 1: Run full shortform tests**

Run:
```bash
./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless '--include=src/features/shortform/**/*.spec.ts'
```

Expected: PASS.

- [x] **Step 2: Run build**

Run:
```bash
npm run build
```

Expected: PASS.

- [x] **Step 3: Run diff check**

Run:
```bash
git diff --check
```

Expected: no output.
