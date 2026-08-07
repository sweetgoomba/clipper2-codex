# Shortform Director Topic-First Research and UI Design

Date: 2026-08-04
Status: Implemented; relevant verification passed

## 1. Goal

Simplify the Shortform Director flow so that users work with topics and video
candidates directly instead of first navigating run-history lists.

The revised product flow is:

```text
operating profile
  → collect current market sources
  → synthesize research topics from market sources
  → choose a topic
  → generate multiple format-diverse video candidates
  → choose a candidate
  → generate the storyboard
```

Reference-video precision analysis no longer participates in topic synthesis or
candidate generation for new runs. It remains stored and readable for backward
compatibility and may later be reused by a separate Shorts-analysis plugin.

This design touches:

- `desktop/clipper_angular`
- `desktop/clipper_nestjs`
- `web/clipper_web_api`

It does not change the storyboard-only downstream boundary.

## 2. Product Principles

### 2.1 Topics are primary; runs are provenance

The Ideas page exists to help a user choose a topic. Research runs are the
source and audit trail behind topics, not the page's primary content.

### 2.2 Candidates are primary; generation runs are provenance

The Candidates page exists to help a user choose a video direction. Candidate
generation runs are shown as origin metadata and through a detail action, not
as a list that must be opened before candidates appear.

### 2.3 Topic discovery and video format are separate decisions

Market sources determine what is timely and worth discussing. The
candidate-generation LLM determines how each selected topic can be expressed as
multiple distinct short-form videos.

### 2.4 Human-readable information precedes technical lineage

Titles, summaries, angles, hooks, outlines, dates, focus keywords, and short
display IDs are visible by default. Full run IDs, artifact IDs, provider
details, and raw lineage remain accessible from expandable technical sections
or detail views.

## 3. Revised Research Flow

### 3.1 Sources retained

New research continues to collect and normalize:

- Google Trends signals;
- Naver News results;
- Naver DataLab data;
- YouTube search results;
- verified YouTube Shorts metadata, including title, description, publication
  time, view count, like count, and comment count when available.

YouTube discovery is not removed. It remains part of market research.

### 3.2 Sources removed from the default topic path

The default topic flow does not fetch or analyze:

- full reference-video media;
- local STT transcripts;
- reference frames and cut measurements;
- comment text;
- hook, structure, pacing, mechanics, or reusable-pattern analysis.

After source normalization, the research run proceeds directly to market-only
topic synthesis. It does not stop in `awaiting_reference_selection`.

### 3.3 Topic synthesis

Topic synthesis receives:

- the selected operating-profile snapshot;
- the optional focus keyword;
- normalized market evidence.

It receives empty reference-pattern and reference-audience inputs. Every topic
must remain grounded in known market-evidence IDs, but no topic is required to
cite a reference pattern or reference-derived audience signal.

The initial research preflight must account for every paid inference call
required to reach the first topic list, including topic synthesis. Users do not
receive a second reference-analysis or reference-skip approval prompt.

## 4. Ideas Page

### 4.1 Profile context

The page header shows the selected operating profile:

- profile name;
- default target duration;
- domain;
- target audience;
- short objective summary;
- `프로필 변경` action.

The user must not need to infer the active profile from a query parameter or
internal profile ID.

### 4.2 Default content

The page loads topics from all completed or partially completed research runs
for the selected profile and displays them newest first.

It does not render `조사 실행 기록` as the primary list.

Each topic card retains the existing human-readable topic content:

- title;
- why the topic matters now;
- suggested angle.

It additionally shows:

- focus keyword, when the source research used one;
- `전체 프로필 조사` when no focus keyword was used;
- research date and time;
- a short display form of the research run ID;
- market-evidence count;
- `조사 내용`;
- `영상 후보 만들기`.

The full run ID remains the internal identity. A deterministic short display ID
is presentation-only and must never be used for API lookup or persistence.

### 4.3 Research detail

`조사 내용` opens a large contextual detail surface without replacing the
topic list:

- desktop: full-height side panel;
- narrow viewport: full-screen dialog.

The detail surface shows the human-readable research evidence and research
report first. Full IDs, provider calls, inference artifacts, raw JSON, and
legacy reference-analysis artifacts are placed under collapsed technical
details.

### 4.4 Add more topics

The page provides a single `주제 추가 생성` action. It opens a choice between:

1. `기존 조사에서 더 만들기`
2. `새 조사 시작`

#### Reuse existing research

The user chooses exactly one existing research run. Combining several research
runs is not supported.

The selector displays each eligible run with:

- focus keyword or `전체 프로필 조사`;
- research date and time;
- short display ID;
- short human-readable source summary;
- existing topic count;
- evidence count.

The selected run's stored normalized evidence is reused. No external market
source is fetched again. The operation receives its own inference-cost
preflight and creates additional topics grounded in the same source research.

Existing topics from that same research run are supplied as exclusions so that
the new batch does not repeat them.

Stored-evidence regeneration is bounded to at most 100 existing topic
exclusions. Once a source research has more than 100 related topics, its
preflight is not ready and the UI directs the user to start a new research
instead. This keeps both the inference input and its cost estimate bounded.

#### Start new research

The existing focus-keyword input and full research preflight are used. New
external market sources are collected before topics are synthesized.

Across different research runs, visually similar topics are not silently
merged because their dates and evidence snapshots differ. Their provenance
metadata lets the user distinguish them.

## 5. Candidate Generation

### 5.1 Autonomous format selection

Candidate generation receives:

- the operating-profile snapshot;
- the selected topic;
- the topic's grounded market evidence;
- candidates already stored for the same topic as duplicate exclusions.

It does not receive or require reference patterns or reference-derived audience
signals.

The LLM is instructed to produce meaningfully different candidates by varying:

- hook;
- format;
- narrative structure;
- promise;
- outline;
- CTA.

The candidate output continues to contain its human-readable `format` string.
No persistent video-formula catalog, formula selector, or formula ID is added
in this scope.

Candidate validation still requires market evidence and rejects unknown
evidence IDs. It no longer rejects a candidate because
`referencePatternIds` or reference-derived `audienceSignalIds` is empty.

`영상 후보 더 만들기` starts another cost-approved candidate-generation
operation for the same topic. Duplicate validation covers candidates already
stored for the topic, not only candidates created within the new operation.

### 5.2 Candidates page

The page header shows:

- selected operating profile;
- selected research topic;
- focus keyword, research date, and short research ID;
- `조사 내용`;
- `다른 주제 보기`.

The default content is every accepted candidate stored for the selected topic,
newest first. The page does not render `영상 후보 생성 기록` as its primary
list.

The existing responsive candidate grid remains:

```css
grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
```

Each candidate card retains:

- format and target duration;
- uniqueness score;
- title;
- Hook;
- Promise;
- Why now;
- CTA;
- full outline;
- `스토리보드 만들기`.

Each card additionally shows:

- generation date and time;
- short candidate-generation run ID;
- `생성 기록 상세`;
- `근거와 과정`.

Evidence IDs, audience-signal IDs, pattern IDs, artifact IDs, and other
technical lineage remain available under the collapsed
`근거 ID와 기술 정보 보기` section. Existing historical candidates may still
show their old audience and pattern IDs there.

## 6. Run and Artifact Compatibility

- Existing research runs and candidate-generation runs are not rewritten.
- Existing topics synthesized with reference patterns remain readable.
- Existing reference-analysis artifacts remain readable from legacy research
  detail.
- Existing candidate sets remain visible in the new aggregated candidate grid.
- New candidate generation ignores historical reference-pattern constraints,
  even when the selected historical topic contains old pattern IDs.
- Candidate and topic runtime projection accepts both the immediately previous
  prompt contracts (`candidate-generation.v1`, `topic-synthesis.v3`) and the
  current contracts (`candidate-generation.v2`, `topic-synthesis.v4`).
- No migration deletes or rewrites local JSON.

Research and candidate details continue to expose the complete underlying run
and artifact lineage. The change is to default navigation and presentation, not
to auditability.

Web API and Desktop releases must be deployed as one coordinated contract
change. Desktop remains able to read prior persisted outputs and resume prior
topic continuations; a continuation that has not yet made its paid inference
call still follows the existing approval credential attached to that run.

## 7. Error and Empty States

- No selected profile: show the existing profile-selection empty state.
- Selected profile with no topics: explain that no topics exist and offer
  `새 조사 시작`.
- Reusing research whose normalized evidence is unavailable or invalid: do not
  silently fall back to new source collection; show a retryable failure and
  offer `새 조사 시작`.
- Additional topic generation with no valid new topics: keep existing topics
  visible and report that no non-duplicate topic was added.
- Topic with no candidates: show the candidate-generation preflight and primary
  generation action.
- Candidate-generation failure: keep earlier successful candidates visible and
  show the failed generation record through the error state and detail action.

## 8. Verification

The implementation is complete only when:

1. a new research run reaches topic synthesis without a reference-selection or
   reference-analysis step;
2. YouTube discovery metadata still participates in normalized market evidence;
3. the Ideas page shows aggregated topic cards before any run-history UI;
4. every topic card shows source research metadata and opens its research
   detail;
5. `주제 추가 생성` can reuse exactly one selected research run without new
   external source calls;
6. `주제 추가 생성` can start a full new research run;
7. new candidate generation succeeds with empty audience and reference-pattern
   inputs;
8. `영상 후보 더 만들기` produces candidates that are checked against
   previously stored candidates for that topic;
9. the Candidates page shows the existing full-detail responsive card grid
   before any generation-run UI;
10. technical IDs are collapsed by default but remain accessible;
11. historical runs, topics, reference artifacts, and candidate sets remain
    readable;
12. relevant Web API, Desktop Nest, and Angular tests and production builds
    pass without paid provider calls.

## 9. Non-Goals

- a reusable video-formula catalog;
- selecting a formula before candidate generation;
- combining multiple research runs into one topic-generation request;
- comment-content analysis during default research;
- audience-question enrichment after topic selection;
- moving reference-video precision analysis into a new plugin;
- modifying storyboard creation or its read-only UI;
- deleting historical reference-analysis code or data;
- implementing actual provider-billing aggregation as part of this UI change.

## 10. Implementation Notes

Implemented on the storyboard-only Shortform Director feature branches on
2026-08-04.

- New research performs the existing market discovery and normalization, then
  persists the market-only continuation policy and publishes topics. It does
  not pause for reference selection. If the process stops between those two
  operations, startup/authenticated read recovery resumes the stored
  continuation without duplicating a completed paid topic call.
- The initial research quote includes the bounded topic-synthesis calls.
- Topic regeneration creates another immutable research run, copies only the
  selected run's stored market-source and normalization artifacts, and passes
  up to 100 existing related topics as exclusions. It does not invoke an
  external source collector; research with more exclusions must start a new
  source collection.
- Profile topics and topic candidates are exposed through read projections;
  historical run and artifact endpoints remain intact.
- Candidate generation explicitly builds a market-only context, including when
  the selected topic came from a historical reference-backed run.
- Failed candidate-generation runs are included in the topic projection with
  their failure artifacts, while earlier successful candidates remain visible.
- The new Angular topic and candidate stores are separate from the legacy run
  stores. This preserves the existing Runs page and historical reference
  inspection while changing the Ideas and Candidates defaults.
- Opening research detail immediately opens its panel and renders loading or
  error feedback inside it. Legacy `reference-analysis` child runs are loaded
  through their dedicated attempt endpoint instead of the parent-research
  endpoint.
- The candidate page retains the original responsive full-detail card grid.
  Source-research and generation details are available as human-readable
  actions; IDs and raw lineage remain in the closed technical-details section.
- Candidate-generation detail selection subscribes to its selected-run signal
  even before the asynchronously loaded candidate collection arrives, so both
  `생성 기록 상세` and `근거와 과정` open from every candidate card.
- No actual-video creation path was added or restored. Candidate selection
  still ends at storyboard creation.

Verification completed without paid-provider E2E calls:

- Web API production build and all 988 unit tests passed.
- Angular production build and all 1,715 tests passed.
- Desktop Nest production build and the 158 Shortform Director affected tests
  passed.
- The complete Desktop Nest suite was also run. It has pre-existing failures
  outside this change in legacy shortform authentication fixtures, TTS mocks,
  repository environment setup, and timing-sensitive Web API client tests.
  No changed Shortform Director test failed.
