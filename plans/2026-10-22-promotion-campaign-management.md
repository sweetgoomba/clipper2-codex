# Promotion campaign management implementation plan

> Historical implementation plan. The final campaign/code rules, merged revisions, and verification are recorded in [the 2026-10-23 current design](../design/2026-10-23-promotion-campaign-current-state.md) and [merge record](../implementation/2026-10-23-promotion-campaign-dev-merge.md). This plan's branch and test notes describe its original execution, not the current `dev` state.

**Goal:** Replace the campaign dropdown with a campaign table and a dedicated detail route; support editing and deleting campaigns under the agreed history rules.

**Architecture:** Keep `/promotions` for the list and `/promotions/:campaignId` for one campaign's codes, report, redemptions, and audit tabs. Reuse the existing right drawer for create and edit. The API owns edit/delete eligibility in a locked transaction; the UI only reflects it.

**Tech stack:** Angular 22, NestJS 11, PostgreSQL, Jest, Karma.

**Global constraints:** Work on the existing `dev` checkouts without discarding local changes. Keep documentation in `.codex`. Preserve the existing campaign and referral data model. A revoked registration still counts as registration history.

## Task 1: API campaign update and delete

- [x] Add failing service tests for full editing before first registration, restricted editing after registration, safe cap changes, delete with and without registration history, and audit records.
- [x] Add failing repository tests for updating a campaign, deleting it with unredeemed codes, and returning a two-code preview plus the total code count in the campaign list.
- [x] Add `PATCH /admin/promotions/:campaignId` and `DELETE /admin/promotions/:campaignId`, both requiring `members.write`.
- [x] Recheck history under the campaign row lock. After registration, allow name, end-date extension, and cap changes; lock start date, tier, duration, credit validity, and history exclusions. Delete only at zero registrations, including revoked registrations; delete unused codes in the same transaction.
- [x] Run targeted API tests and build.

## Task 2: Campaign table and editor

- [x] Add failing admin tests for the all-campaign table, status/period/tier/registration columns, two-code preview with `+N`, detail link, edit drawer prefill, and delete disabled when registrations exist.
- [x] Replace the dropdown with a table at `/promotions`; show the create button there. Reuse the existing right drawer for edit and create, with locked fields explained after registration.
- [x] Confirm deletion with the number of issued codes; handle server conflict if a registration occurs while confirmation is open.
- [x] Run targeted admin tests.

## Task 3: Detail navigation and verification

- [x] Add the `/promotions/:campaignId` detail route and back navigation; move codes, reports, registration/revocation, and audit into tabs.
- [x] Verify list data, route navigation, the edit drawer, and the report tab in the running local admin UI.
- [x] Run focused API and admin tests, builds, and diff checks.

## Verification

- API service and repository: 25 tests passed; Nest build passed.
- Admin promotion and audit labels: 22 tests passed; Angular build passed.
- Local `/promotions` loaded live tier names and the first two codes after API restart. The campaign detail link, back navigation, and report tab worked.
