# Return to the previous page after web login

User request: login from the client home/public page should return to that page, not always /my. Work on fix/web-login-return-page in client and Web API from latest origin/dev. Inline execution using Superpowers systematic debugging, writing-plans, TDD and final review. No commit/push/deploy requested yet.

## Findings and design
Header login link omits returnUrl. Client and server sanitizeWebReturnPath allow /my and bounded /pricing destinations but reject the home page. OAuth callback and signup ticket apply the server validator, so frontend-only changes cannot fix the flow.
- Carry the current URL through header login, OAuth callback and signup completion. Preserve query and fragment (e.g. /#price).
- Allow only existing public content paths /, /pricing, /terms, /privacy, /refund plus existing /my destinations. Keep subscription-code validation and reject external, protocol-relative, backslash and authentication-loop targets.
- With no usable return address, go home (/).
- Existing explicit checkout and Free-plan actions still carry their intended /my destination.
- Keep the existing callback origin restriction, signing, token placement and server authentication logic unchanged.

## Task 1: Browser return routing
Files: client core/api/auth-api.service.{ts,spec.ts}, shared/layout/app-header/app-header.component.{ts,html,spec.ts}, public/login/login.component.spec.ts, public/auth-callback/auth-callback.component.spec.ts, core/auth/auth-token.interceptor.{ts,spec.ts}.
- [x] Add failing tests for home/query/fragment links, normal login fallback, successful callback destination, unsafe URL rejection and expired-session return.
- [x] Implement URL carry-forward and conservative public-path validation.
- [x] Run client focused/full suites, build and actual browser header-link smoke.

## Task 2: Server preservation
Files: Web API auth/application/web-return-url.{ts,spec.ts}, presentation/web-login-flow.spec.ts, signup-flow.spec.ts.
- [x] RED: home/public destinations survive normalized callback and signup ticket including nested fragments; default home and external targets still cannot receive tokens.
- [x] Apply matching allowlist/default/fragment preservation.
- [x] Run auth-focused/full server tests, build and independent review of both sides.

## Review focus
External destinations; login/callback loops; pricing checkout validation; nested fragments vs token fragment; first signup vs existing-account login. Every path remains relative to the application origin.

## Verification and review
- RED: client routing tests failed 27/56; interceptor failed 2/6; API return-path/OAuth/ticket tests failed 43/66; signup flow failed 3/13 for the expected old /my fallback or dropped hash.
- GREEN: client full suite 606 passed; API 471 suites / 5,163 passed, 109 skipped; 5 snapshots passed. API focused auth suite 79 passed.
- Builds: API npm run build exit 0; client ng build --configuration=prod exit 0. Initial bundle warning 510.70 kB / 500 kB remains (not an error).
- Actual localhost:4201 home /?campaign=launch#price login link navigates to /login?returnUrl=%2F%3Fcampaign%3Dlaunch%23price. Running localhost:3000 OAuth start returns signed state carrying the same callback destination. No real Google provider login or signup was performed.
- Independent read-only review: no actionable findings. Reviewer exercised actual client/server sanitizers with 32 normal/adversarial cases: zero mismatches; all callbacks remain on the configured origin with no outer hash.
- Removed an inconsistent preexisting fallback assertion for a foreign callback with explicit /my: source and the adjacent test already normalize its origin and preserve the allowlisted destination. Production normalization policy remains unchanged.
- Initial implementation was left uncommitted until the user requested integration into the refund session branch.

## User-requested integration into refund session branch
- User requested merge into the branch used by 고객 환불·외부 취소 설계 독립 검증 (thread 01a19e06-16f8-75d1-ba54-0514b52e8414). Read thread context and verified the active client/API worktrees are pg-ops-20261103. No thread messages sent.
- Re-ran source full suites before committing: client 606 passed; API 5,163 passed, 109 skipped, 5 snapshots.
- Source commits: client 2d5cc51, API a5916e9 on fix/web-login-return-page.
- Merged into pg-ops-20261103 in /Users/jina/project/adlight/.worktrees/pg-ops-20261103-client (916d617) and /Users/jina/project/adlight/.worktrees/pg-ops-20261103-api (903953a). No push requested or performed. This also brings their missing dev ancestry: dashboard plan summary and artist-matcher improvement.
- Target work was unstaged before integration. Temporarily stashed only four overlapping dashboard files, merged, applied the exact stash without conflict, verified all original added/removed dashboard lines match, then dropped only that temporary stash. Other 17 client files and all 134 existing API files have identical SHA-256 hashes before/after. No existing refund work was committed or discarded, and target indexes remain empty.
- Merged working tree verification: client full suite 625 passed; API 485 suites / 5,301 passed, 140 skipped, 5 snapshots passed. Client prod build and API build both exit 0. Client initial bundle warning 512.07 kB / 500 kB. git diff --check clean in both targets; source commits are ancestors of target HEADs.

## Runtime correction after user reproduced /my on port 4203
- 4203 serves the pg-ops client worktree and its local environment calls localhost:3311 (not the previously checked 3000 API).
- Reproduced actual 3311 OAuth start with inner /#price: signed state carried http://localhost:4203/auth/callback?returnUrl=%2Fmy. Process43266 was node dist/main started before the merge; rebuilt files on disk were current but the running Node process retained its loaded old sanitizer.
- Verified the existing launch script /private/tmp/adlight-refund-ui-api.sh and the old process's non-secret PORT, database names, CORS, callback and feature flags matched. Terminated only43266 and restarted the same script using Node24.19.0. Current API process20043, exec session65137, log /private/tmp/refund-row-api-login-return.log. No source/environment/database changes.
- GREEN runtime check: actual3311 OAuth start preserves http://localhost:4203/auth/callback?returnUrl=%2F%23price and /health returns200. Actual4203 browser header from /#price navigates /login?returnUrl=%2F%23price. Real Google provider login was not performed.
- Earlier runtime verification checked3000 and missed this already-running3311 instance.

## User-requested dev integration and push
- User requested merging login-return fix into dev and pushing both repositories. Fetched latest origin/dev; both source checkouts were clean and each contained only the login-return commit above dev. Kept pg-ops worktrees and their refund changes untouched.
- Merged fix/web-login-return-page into dev: client33cea7d, API9dad6e0. Both merge trees equal the independently reviewed feature trees.
- Fresh verification on dev: client606 tests passed; API471 suites / 5,163 tests passed,109 skipped,5 snapshots passed. Client prod build and API build both exit0 (existing client initial budget warning510.70kB/500kB).
- git push origin dev succeeded in both repositories: client f52e731..33cea7d; API bf8e452..9dad6e0.
