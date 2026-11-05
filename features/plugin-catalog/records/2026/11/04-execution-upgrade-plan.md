# Plugin execution entitlement and upgrade implementation plan

> For agentic workers: focused repository tasks with TDD; no commits/pushes/merges or real payments.

**Goal:** Check current plugin eligibility before credits at billable events and connect denied users to the right subscription or plan-change flow.
**Architecture:** Web API is execution/payment authority. Preserve admitted-run idempotency and queue debit timing. Desktop reuses public plugin-plan catalog and authenticated web handoff. Shared pricing reuses the existing /my quote/consent/confirmation flow.
**Tech Stack:** Angular 22, NestJS, TypeScript, Jest, node:test, Karma.
**Spec:** User requirements and accepted playback in this chat; independent read-only verification chat 01a1a3a2-09dd-7d73-bbe0-8c100795ae9e, completed before implementation.

## Global constraints
- Installation/entry, admin settings/store badges, billing arithmetic, plan-change policy, refunds and admitted-run recovery remain unchanged.
- No commits/pushes/merges or real payment/provider calls.
- Effective access is separate from subscription. Promotion/admin access never becomes a paid subscription implicitly.
- Active subscription is required for changes; annual-to-monthly is forbidden; lower-rank change is scheduled.
- Exact allowed sets drive explanations. Only a complete suffix of distinct ranks is labelled “이상”. Unsold tiers are not promised as immediately purchasable.
- Preserve existing quote numeric fields; resolve plugin permission before reading balance, compare credits only when entitled.
- Additive API fields are reflected in OpenAPI and relevant types/mocks.
- Matching feat/plugin-execution-upgrade branches in four clean existing checkouts; no worktree setup needed for this repository-separated change.

## Review focus
- Rights and credits both insufficient: rights first; no charge/new execution.
- Rights change after consent including async explainer: accurate upgrade path.
- Login/restoration/foreground return cannot accidentally create a duplicate subscription.
- Non-contiguous entitlements/unsold tiers/deferred changes never promise instant access.
- Already charged queue/recovered attempt continues without a second charge or re-admission.

## Task 1: Server admission and denial propagation
**Owns:** web/clipper_web_api and desktop/clipper_nestjs.
**Consumes:** Existing effective access, catalog and operation admission.
**Produces:** Permission resolved before balance in quote, numeric contract unchanged. Expose quote pluginKey through local types. Start denial includes safe details.pluginKey/operationKey preserved through local 403 projection. Storyboard start distinguishes permission from insufficient credits. Explainer quote returns existing credits plus operationKey/pluginKey/canStart/reason/balances. Async explainer failures preserve machine-readable PLUGIN_NOT_ALLOWED code/marker in stored errors/events/scenes for app consumption. Preserve queue and payment timing.
- [x] Add regression tests for order/precedence/details/storyboard reason/explainer quote+async denial, observe expected RED.
- [x] Contract first, minimal code, targeted tests and backend builds GREEN.
- [x] Report changed files, exact test commands/counts and limits; no commit.

## Task 2: Subscription-aware shared web pricing
**Owns:** web/clipper_web_client.
**Consumes:** Existing access/subscription/catalog and /my change flow.
**Produces:** Cards represent loading/error, visitor/free, current exact product, active upgrade/cycle change, scheduled downgrade/target, forbidden annual-to-monthly, blocked subscription and promo/admin management. Recheck account before actions. Free uses initial checkout; paid changes preserve selected product through login/redirect and open existing /my consent flow without autocharge. /pricing?plugin=<key> identifies exact allowed plans. Legacy existing-subscriber checkout redirects to change review. Refresh account after completion/return.
- [x] Behavioral RED tests for routing, card states, fetch failure, target handoff and consent.
- [x] Minimal implementation; focused Karma (coordinate single frontend slot) and build GREEN.
- [x] Parent broad verification; no commit.

## Task 3: Desktop upgrade modal and custom execution paths
**Owns:** desktop/clipper_angular.
**Consumes:** Task 1 additive fields, existing /access/plugin-plans and /access/current, quote and web handoff.
**Produces:** Shared PluginUpgradeService used by common guard, storyboard and explainer actions/failures. Exact allowed-plan explanation and /pricing?plugin=<encoded key> handoff. Upgrade CTA never means execution consent. Synchronous start denial and asynchronous explainer/event/scene failure use the same guidance. Fresh server permission check on retry; cached account/prices cannot deny execution. Correct storyboard reason and explainer quote types. Accept older allowed quote fixtures and stored errors; missing denial metadata falls back to generic pricing without guessing a tier. Preserve existing credit confirmations/lifecycle.
- [x] Behavioral RED tests for sets, blocked+low credits, link, fresh retry, storyboard and explainer failures.
- [x] Minimal dialog/integrations; coordinate Karma with parent, targeted tests/build/style checks GREEN.
- [x] Report files/tests/limits; no commit.

## Integration
- [x] Review all diffs/contracts/mocks; full affected backend and sequential frontend tests/builds/style guards.
- [x] Local UI/runtime smoke with mocks/read-only data; no charges/provider calls.
- [x] Fresh implementation reviewer; fix important findings with regressions.
- [x] Record completion and leave reviewable uncommitted feature branches.

## Interface pre-flight
Task 1 -> Task 3: optional pluginKey, additive explainer quote fields, safe 403 details; PLUGIN_NOT_ALLOWED stable stored marker. Task 3 supports older stored marker fallback.
Task 2 <-> Task 3: /pricing?plugin=<encoded key>; web chooses fresh actual purchase/change path.
Repository ownership does not overlap. Frontend Karma is serialized.

## Progress
Independent review completed before implementation; incorporated effective access vs subscription, active-only changes, exact sets/unsold tiers, sync+async denials and queue-specific admission. Existing main API baseline 4 suites/308 passed; reviewer reports 7 suites/381 passed.

Implementation dispatch: backend_entitlements owns both backend repos; web_pricing owns web client; desktop_upgrade owns Angular desktop. Parallel scope is disjoint. Desktop observed meaningful RED 3 failures/269 success; web observed RED 13 failures/130 success. Frontend Karma serialized. Parent isolated Playwright baseline independently reproduced Basic paid user seeing Pro 시작하기.
Integration finding: both client auth-api.service.ts and server auth/application/web-return-url.ts reject pricing?plugin=...; owners are adding narrow validated plugin query support.
Backend additive async interface confirmed: project.lastError/event.error/video.error retain canonical PLUGIN_NOT_ALLOWED; ingredient.error/keyframe.error/changeFrame.error now optionally preserve that marker. Parent read backend source diff, no admission/queue timing redesign.

## User-added final integration gate (2026-11-04)
After implementation and verification finish, create a NEW separate user-visible Codex chat for independent read-only verification of the FINAL working-tree implementation. The earlier preimplementation review and in-session reviewer do not replace this gate. Reflect actionable findings and rerun affected verification. Report the final independent outcome to the user before any dev integration. Do not commit, push or merge dev without a subsequent explicit user instruction.
- [x] Final implementation/test outcome recorded.
- [x] New separate final-verification chat created and completed.
- [x] Findings adjudicated, required fixes applied and verified.
- [x] Results reported, feature branches preserved; no dev merge.

Final separate verification chat completed its initial review: one confirmed P2 at app stageHasNoNewWork, where failed changeFrame is treated as paid despite backend startKeyframes counting pending changeFrame only. Natural compiled-server reproduction reports zero image/billing calls and free transition. Accepted after root source verification; desktop_upgrade assigned narrow RED->GREEN fix with pending/individual regeneration counterexamples, followed by scoped re-verification in the SAME new chat. Independent tests: API155/local194/recovery30/app496/web148 passed. Entire app suite remains not fully green (one async template-upload failure); verifier found no causal feature evidence but did not claim experimental baseline equivalence.

Final gate complete: new visible chat 01a1a3bd-9925-77f1-bf27-84e696320c74 independently verified implementation, found one P2, and independently reverified its two-file fix (282 tests + natural server reproduction + 18-state matrix PASS). Final full app10769 PASS; all four repository suites/builds/diff-checks green, existing API skips and historical flakes retained in result. No merge/commit/push. See 04-execution-upgrade-result.md and 04-execution-upgrade-final-independent-review.md.
