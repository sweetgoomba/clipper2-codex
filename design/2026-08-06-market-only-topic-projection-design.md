# Market-only topic projection contract repair

## Problem

Market-only topic synthesis supplies no reference analysis data, so valid
`topic-synthesis` output contains empty `audienceSignalIds` and
`referencePatternIds` arrays.

The Web API response schema and prompt allow and require those arrays to be
empty when the corresponding inputs are absent. The Desktop Nest response
projector currently requires at least one item in both arrays, rejects the
valid Web API response, and returns
`SHORTFORM_DIRECTOR_INFERENCE_RESPONSE_PROJECTION_INVALID`.

## Design

Keep the existing strict response projection and align only the two incorrect
array bounds with the Web API contract:

- `evidenceIds` continues to require at least one item.
- `audienceSignalIds` allows zero items.
- `referencePatternIds` allows zero items.

No endpoint, response envelope, persisted artifact, prompt, provider call, or
UI behavior changes.

## Test

Add a Desktop Nest regression test that projects a valid `topic-synthesis`
response containing a grounded topic with non-empty `evidenceIds` and empty
reference-derived ID arrays.

The test must fail with the current projector, then pass after the two minimum
item bounds are corrected. Existing rejection coverage for malformed inference
responses remains unchanged.

## Out of scope

- Re-running a paid provider request.
- Changing research failure diagnostics or UI error presentation.
- Relaxing evidence grounding.
- Refactoring the projector or synchronizing contracts through a new shared
  package.
