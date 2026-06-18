# Render Provider Registry Boundary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preserve `VideoRenderProviderRegistry` as Template Builder sample render infrastructure while keeping old generic render-job persistence removed.

**Architecture:** Add a small contract test around `TemplateBuilderSampleRenderService.start()` proving sample render resolves a provider through the registry and executes it directly. Do not reintroduce persisted render job DTOs, services, repositories, routes, or Angular callers.

**Tech Stack:** NestJS TypeScript services, Node `node:test`, existing Template Builder DTO fixtures.

---

### Task 1: Contract Test

**Files:**
- Modify: `clipper_nestjs/test/template-builder-api.test.js`

- [ ] **Step 1: Write the failing test**

Add a test that constructs `TemplateBuilderSampleRenderService` with a fake provider registry, calls `start()` with `createDefaultTemplateVariant(...)`, and asserts:
- `resolve()` receives provider id `video.render.legacy_clipper1.python_worker`
- `render()` receives a sample render job id and output root
- no persisted render-job API/service is involved

- [ ] **Step 2: Run test to verify RED**

Run: `node --test test/template-builder-api.test.js`

Expected: fail until the assertion names/contract are wired correctly.

- [ ] **Step 3: Keep implementation minimal**

If the test reveals only missing explicit contract, update test expectations or small naming/documentation only. Avoid changing provider resolution behavior unless the test exposes an actual bug.

- [ ] **Step 4: Verify GREEN**

Run:

```bash
npm run build
node --test test/template-builder-api.test.js test/project-output-render-path.test.js test/simplified-shortform-render-recipe-provider.test.js
git diff --check
```

- [ ] **Step 5: Commit**

Commit NestJS changes and `.codex` docs separately.
