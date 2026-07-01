# Dance Member Profile And Manual Mapping

Date: 2026-07-01

## Goal

Make Dance Highlight usable when the upstream group member list includes inactive members, and when automatic face matching leaves a real member as an anonymous `person_N`.

## Decisions

- Existing dance projects and reference cache are discarded; no migration path is needed.
- The saved per-artist data becomes an artist member profile, not only a reference-image cache.
- A profile stores the included members, excluded members, and selected reference images for included members.
- Subsequent runs for the same artist reuse the saved included members and selected images, so the image-selection step remains skipped.
- Users can manually assign an anonymous result person to an included member after a project completes.
- Manual assignments are saved as project-level overrides and applied when building project detail; clip files are not regenerated.

## Runtime Flow

1. User detects and confirms an artist.
2. Backend resolves all members and returns a saved profile if one exists.
3. If the profile is complete, Angular uses the profile's included members and selected images, then starts the pipeline.
4. If no complete profile exists, Angular shows a member profile step where the user includes or excludes resolved members.
5. Angular loads images only for included members.
6. The pipeline receives `dance_setup.members` for included members only and `dance_setup.excludedMembers` for audit/debug.
7. Backend saves the submitted profile from job params.
8. Project detail applies automatic mapping first, then project-level manual assignments.

## Backend Shape

`dance/reference-cache.json` remains the storage file for now, but its entries become profile entries:

```json
{
  "version": 2,
  "subjects": {
    "local": {
      "qid:Q000": {
        "artistName": "LE SSERAFIM",
        "artistQid": "Q000",
        "artistType": "group",
        "includedMembers": [
          {
            "memberKey": "huh_yunjin",
            "memberName": "허윤진",
            "selectedImages": []
          }
        ],
        "excludedMembers": [
          {
            "memberKey": "kim_ga-ram",
            "memberName": "Kim Ga-ram"
          }
        ],
        "updatedAt": "2026-07-01T00:00:00.000Z"
      }
    }
  }
}
```

Project-level manual assignments live in `ProjectSnapshot.result.dance_member_assignments`:

```json
{
  "person_1": {
    "memberKey": "허윤진",
    "memberName": "허윤진",
    "updatedAt": "2026-07-01T00:00:00.000Z"
  }
}
```

## UI

The member-image step gains an include/exclude section above image cards. Excluded members are shown there but do not require image selection. When a complete profile exists, this page is skipped.

The dance result sidebar shows an action for anonymous persons, letting the user assign them to one of the included members without clips. Saving reloads project detail so the anonymous row is merged into the chosen member.

## Verification

- Backend unit tests cover profile lookup/save and manual assignment persistence.
- Angular tests cover first-run exclude flow and cache-hit profile reuse.
- Project detail tests cover anonymous `person_N` being renamed/merged into the selected member.
