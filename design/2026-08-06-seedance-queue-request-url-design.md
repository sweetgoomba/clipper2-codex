# Seedance Queue Request URL Fix Design

## Problem

Seedance 2.0 jobs are submitted to:

`https://queue.fal.run/bytedance/seedance-2.0/text-to-video`

fal.ai returns queue operation URLs under the parent endpoint:

`https://queue.fal.run/bytedance/seedance-2.0/requests/{requestId}`

The current transport incorrectly appends `/requests/{requestId}` to the
submission URL, retaining `/text-to-video`. fal.ai responds to status requests
on that incorrect URL with HTTP 405, which the Web API exposes as a provider
502. Successfully queued, processing, or completed jobs therefore appear to
have failed.

## Design

Keep two explicit URL roots in `SeedanceVideoTransport`:

- Submission root: `https://queue.fal.run/bytedance/seedance-2.0/text-to-video`
- Queue request root: `https://queue.fal.run/bytedance/seedance-2.0`

Submission continues to use the text-to-video endpoint. Status inspection uses
`{queueRequestRoot}/requests/{requestId}/status`, and result retrieval uses
`{queueRequestRoot}/requests/{requestId}`.

This preserves the existing persisted job contract. Existing jobs only need
their stored fal.ai request ID, so no database migration or resubmission is
required.

## Error Handling

Existing HTTP and response normalization remains unchanged. The fix only
corrects which fal.ai resource is queried.

## Verification

The transport test must independently assert all three observable URLs:

1. Submission retains `/text-to-video`.
2. Status lookup excludes `/text-to-video`.
3. Result lookup excludes `/text-to-video`.

The test must fail against the current implementation before the production
constant is changed.
