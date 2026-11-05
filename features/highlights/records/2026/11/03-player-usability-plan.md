# Highlight player usability implementation plan

> **For agentic workers:** Use superpowers:executing-plans in this session. No commits or push without user request.

**Goal:** Consistent playback shortcuts, usable audio controls, unrestricted source playback while editing, and fast artist detection.
**Architecture:** Extend SourceSceneOverlayComponent; prefilter unmatched artist aliases before Unicode regex matching.
**Tech Stack:** Angular 22, Material, TypeScript, NestJS, Karma/Jasmine, Jest.
**Spec:** 03-player-usability-design.md (user approved).

## Global Constraints
- Branch feat/highlight-player-usability from latest origin/dev for UI and Web API.
- Preserve API contracts, matching results/order, existing visual tokens and normal scene playback limits.
- No unrelated refactor, commit, push, deployment, or dependency changes.

## Review Focus
- Focused next/previous/edit buttons and repeated Space must not trigger their default action.
- Inputs, checkboxes, and composition must retain native keyboard interaction.
- Source/legacy players must retain audio settings across scene changes.
- Seeking then requesting playback in edit mode must resume outside the selected range.
- Unicode boundaries, aliases and result ordering must be identical after optimization.

### Task 1: Scene playback and audio
**Files:** clipper_angular/src/shell/projects/source-scene-overlay/source-scene-overlay.component.{ts,html,scss,spec.ts}
**Interfaces:** existing input/output APIs unchanged; private playback/audio state stays in this component.
- [x] Add regressions for Space default prevention, repeat/input guards, editing before/after selected bounds, deferred edit seek playback, volume and mute with source/legacy players and navigation.
- [x] Run Karma against the component; confirm expected failures before implementation.
- [x] Add keyboard routing, edit-mode boundary exemption and seek resumption; add accessible volume slider/mute and volumechange synchronization.
- [x] Run affected component suites, style guards, build and runtime smoke. Expected: all affected tests pass, build renders.

### Task 2: Artist detection
**Files:** clipper_web_api/src/modules/dance-catalog/application/artist-matcher.{ts,spec.ts}
**Interfaces:** detectArtists(artists, title) and searchArtists unchanged.
- [x] Add Unicode/word-boundary examples and a regression using the full bundled catalog with a generous 1000ms budget.
- [x] Run Jest; confirm performance regression fails on current code.
- [x] Skip wholeWord when the cleaned title does not contain the normalized alias.
- [x] Run dance-catalog suites, build and remeasure the same catalog/title. Expected: matching unchanged, computation below 1 second.

## Progress ledger
Pre-flight: tasks share no interfaces.
Ruling: implement inline in existing clean checkouts on user-requested feature branches; no worktree or commits are needed.
Baseline: Web API matcher/query 8 tests pass. Angular crashes in sandbox native build; retry outside sandbox in progress.

## Verification and review notes
- Initial UI baseline: source overlay + dance-flow 109/109 pass. Web matcher/query baseline 8/8 pass.
- Task 1 RED: 8 failures reproduced (bounds, seek resumption, Space, audio).
- Task 2 RED: full-catalog detect 8640.7ms exceeds 1000ms budget. GREEN: dance-catalog 138/138 pass; same title/catalog 15–34ms over five runs; candidate QIDs unchanged (Q109375061, Q112965877).
- Web API full suite: 471 suites pass, 11 skipped; 5144 tests pass, 109 skipped; 5 snapshots pass. Build passes.
- UI whole suite before review follow-up: 10664 pass, 2 fail: ProjectCardComponent dark/light completed card colors; StoreComponent install-all disappearance vertical alignment. Both pass in isolated combined run (165 existing tests pass; only two newly added review regression assertions fail as expected).
- Review: independent read-only reviewer finds queued play cannot be canceled during seek (Important) and Shift+Space interception (Minor). Both reproduced via regression tests before changes. Ruling: include Shift in modifier guard as part of keyboard consistency; cost is that Shift+Space stays native rather than controlling playback.
- Review fix: toggle cancels pending playback as well as actual playback. Space regression fixture now explicitly completes initial automatic playback request before testing paused playback.
- Browser smoke with generated 30-second video and actual production component: focused next-button Space plays without navigation; .35 volume + mute persists to scene 2; edit scene 12–17 sec seeks to 20.08 sec and plays at 20.32 sec without jumping back. Dark/light screenshot inspection passes.
- Temporary harness/main replacement, generated video, browser tab and dev server cleaned up; original main.ts restored byte-for-byte. Final diff limited to source overlay TS/HTML/SCSS/spec and artist matcher TS/spec.
- Final local UI build passes; styles 21/21 pass. Final affected UI regression run: 412/412 pass, including both review regressions and the two whole-suite failures in isolation.
- Ruling: leave code changes uncommitted on requested feature branches (repo policy); no merge, push or deploy requested.

## Dev integration (2026-11-03)
User explicitly requested committing UI and Web API, merging into dev, and pushing. Re-fetched both origin/dev: no additional upstream changes. Fresh verification: affected UI 412/412, dance-catalog 138/138 pass.
- UI implementation d9e51c68; dev merge 500cf9f4; origin/dev pushed successfully.
- Web API implementation 3fbf1ba; dev merge bf8e452; origin/dev pushed successfully.
- Local dev first fast-forwarded to fetched origin/dev in each repository. No merge conflicts. Merged trees match verified feature-branch trees exactly. Feature branches retained locally. No deployment requested or performed.
