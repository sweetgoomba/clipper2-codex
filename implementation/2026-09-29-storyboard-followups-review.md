# Storyboard follow-up review

Reviewed the uncommitted source and relevant test diff against PLAN.md, W07, and the team spec D6–D13/section 5. Baselines: Angular 797782e8, Nest 824a7a9f, Web API 31f4482. Runtime symlinks and generated output were excluded. Read-only review; no builds, provider requests, external network, or database operations were run.

## Critical

None found.

## Important

1. **Freeze the profile IDs shown in the delete confirmation.** `desktop/clipper_angular/src/features/shortform-director/pages/profiles-page/profiles-page.component.ts:204` computes deletion IDs after awaiting the confirmation at line 201. The backing selection retains IDs that are temporarily hidden by the busy filter (line 116). Select A and B, let B become busy before opening the dialog (which approves A only), then let B become eligible while the dialog is open. Accepting the one-profile confirmation deletes both A and B. This was reproduced by extracting/transpiling the actual method without changing the checkout: `dialogTitle="프로필 1개를 삭제할까요?", confirmedCount="1개", deleted=["one","two"]`. Capture IDs and displayed counts before opening the dialog, use that fixed set after acceptance, and keep the existing per-ID busy recheck. Add a deferred-confirmation regression covering eligibility returning while the dialog is open.

## Minor

1. **Canceled in-flight inference has no elapsed-time event.** `desktop/clipper_nestjs/src/modules/shortform-director/application/storyboard-stage-retry.ts:53` rethrows an aborted signal before the timing diagnostic at line 54. Retry-wait cancellation and source cancellation are measured, but cancellation during an inference attempt leaves its duration absent. An optional safe cancelled timing event before preserving the existing abort throw would close the measurement gap without changing retry or settlement semantics.

## Declined to judge

- Actual provider latency, generated quality, provider rate limits, and live credit settlement: excluded by the task's no-provider/no-database verification scope; fixture timing cannot establish them.
- Native Korean IME behavior for all OS/browser event sequences: the composition lifecycle and DOM regression cases were inspected, but no native IME session was performed by this reviewer.
- The pre-existing canceled/partial-result archive creation policy and the global JobHistoryService subscriber ownership contract: unchanged shared state machines outside this diff; the new deletion persistence and recovery paths were traced against them.
- Complete suite execution and production rollout: concurrent verification belongs to the implementers; this reviewer ran diff checks and the focused read-only confirmation reproduction only.
- The already identified menu backdrop propagation and danger-token styling issues: actively owned by the root implementer and intentionally excluded from duplicate findings.

## Readiness

**With fixes.** Fix the confirmed Important deletion race and verify its regression before integration. No additional must-fix finding was identified in owner/busy checks, shared generation/recovery locking, tombstone/index crash repair, preserved documents/snapshots, legacy route/PDF retirement, progress checkpoint ordering, partial settlement, or read-time ledger naming. `git diff --check` passed in all three repositories at review time.

## Resolution recheck

Both findings above are **resolved** in the subsequent source and test changes, inspected read-only.

- The FE captures `ids` and the retained storyboard count before opening the confirmation and uses the frozen IDs for both the dialog and deletion. The per-ID busy recheck still runs immediately before each DELETE. The new deferred-confirmation regression reproduces the original hidden-selection transition and asserts that only the displayed profile is deleted; the newly eligible profile remains.
- Retry cancellation emits `storyboard.stage.cancelled` through the existing guarded diagnostic helper before calling the unchanged `signal.throwIfAborted()`. Its fields contain batch/stage identifiers, attempt, and elapsed time only. The new regression checks exact abort-reason identity, one provider call, one reservation, zero waits, no provider/abort-reason content, and the same outcome when the logger throws.

The implementer reports the deferred-confirmation case failed before the FE fix and the final Angular whole suite passed 5,395 tests. Those runs and browser fixture QA were not repeated by this reviewer, as requested.

**Updated readiness: Ready within the reviewed scope.** No unresolved Critical, Important, or Minor finding remains. The live-provider, native-IME, live-database, unchanged shared-policy, and rollout limitations listed above remain unchanged.



## 제작 목적·이름 후속 리뷰

Critical/Important없음. Minor: native maxlength UTF-16와 API codepoint 차이는 기존방식에서이어짐. 최신검증/판단범위는 목적 UX 보고서 및 worktree REVIEW.md 참조.
