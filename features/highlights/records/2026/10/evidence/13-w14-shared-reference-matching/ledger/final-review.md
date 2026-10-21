# Independent review — 2026-10-13

Reviewer: /root/shared_face_review, gpt-6-astra, fresh context, read-only.
Initial selected suite independently rerun: 68 passed.
Critical: none. Important: 3. Minor: none.

1. gallery.py normalized centroid validation: near-opposite valid B samples
   (1,0),(-1,.0001) create norm .99997997, causing matching to reject all references.
   Fix: validate computed centroid, retain invalid_centroid failures for affected
   samples, preserve valid A and the legacy mean/L2 formula.
2. examples/reference_matching.py: conflicting observation IDs across scopes or
   unscoped queries bypassed consensus-local validation.
   Fix: validate complete query batch, reject conflicting fingerprints and deduplicate
   identical observations before matching and partitioning.
3. replay.py: missing association defaulted to confirmed.
   Fix: require explicit association, retain recorded legacy assumption in actual
   data and explicitly annotate synthetic fixtures.

Reviewer's assessment: ready with fixes. No second review dispatched.
Parent verification: five new cases failed before implementation (5 failed/20
passed), then selected suite 73 passed. Final broader run 617 passed/3 skipped,
11 real-plugin boot smoke cases excluded; donor compatibility 27 passed.

Declined to judge:
- Independent recognition/face ownership quality without new held-out labels.
- Dance/Person product integration and plugin environment installation.
- Windows execution.
- Legacy grouping/detector policy changes (behavior preserved).
- External supervisor enforcement and unrelated broader-suite failures (parent
  checked separately; local-port restrictions reproduced, rerun documented).
