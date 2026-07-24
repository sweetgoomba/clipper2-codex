# Shortform Director quality-input experiment

Offline-only workspace for validating frozen four-case source packs before any
provider, Vira, database, or production integration work.

## Current boundary

The four packs and Vira export/normalization code are fixture-validated
artifacts. They are not evidence that the current Vira service or database has a
representative market corpus.

As of 2026-07-24:

- the actual Vira database was not queried;
- all four case Vira files remain `provider_not_called` with empty evidence;
- the prepared `shorts_*` SQL must not be run against the current test database;
- the four fixed topics are not approved Vira collection seeds;
- no Vira-dependent generation condition may run until a representative corpus
  strategy is separately designed and approved.

See
`../../design/SHORTFORM_DIRECTOR_VIRA_VALIDATION_CORPUS_OPTIONS_2026-07-24.md`
before resuming Vira work.

Each case directory must contain exactly these eight JSON files:

- `manifest.json`
- `profile.json`
- `episodes.json`
- `source-cards.json`
- `audience-cards.json`
- `reference-cards.json`
- `vira-evidence.json`
- `feedback-cards.json`

Validate the four packs with:

```sh
node scripts/validate-packs.mjs --sealed cases/beauty-01 cases/product-01 cases/idol-01 cases/expert-01
```

The validator reads only regular files located below this experiment workspace;
it refuses symbolic links and does not print source content.
