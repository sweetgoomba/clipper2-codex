# Shortform Director Eight Diverse Topics Design

Date: 2026-08-06
Status: Implemented; relevant verification passed

## 1. Goal

Each initial research run and each stored-evidence topic regeneration produces
eight grounded topic choices instead of leaving the count to the inference
model.

The eight topics must be meaningfully different. When the user supplied a focus
keyword, every topic must address that keyword directly rather than filling the
list with broadly related profile topics.

This design touches:

- `web/clipper_web_api`
- `desktop/clipper_nestjs`

It does not change the Ideas page layout, the number of provider calls, source
collection, or candidate generation.

## 2. Approaches Considered

### 2.1 Prompt-only count

Ask for eight topics in the system prompt without changing the response schema.
This is the smallest change, but the model may still return a different count.

### 2.2 Variable five-to-eight count

Allow the model to return fewer topics when evidence is limited. This reduces
the chance of weak topics but reintroduces the inconsistent result count that
the change is intended to remove.

### 2.3 Exact count in prompt and contract

Require exactly eight topics in both the system prompt and the structured-output
schema. This gives the UI a predictable batch size and makes contract drift
fail visibly instead of silently publishing a short list.

Approach 2.3 is selected.

## 3. Topic Synthesis Contract

The Web API topic-synthesis contract advances from
`shortform-director.topic-synthesis.v4` to
`shortform-director.topic-synthesis.v5`.

The v5 prompt requires:

- exactly eight topics;
- no repeated topic or angle, including near-duplicate title rewrites;
- meaningful variation in viewer question, explanatory angle, use case,
  comparison, failure mode, trade-off, or debate;
- at least one supplied market-evidence identifier for every topic;
- direct relevance to `focusKeyword` for every topic when it is present;
- no unrelated or unsupported topic added merely to reach eight.

The v5 JSON schema sets both `minItems` and `maxItems` for `topics` to eight.
The Web API manual validator and Desktop response projector mirror the same
bound.

Existing grounding rules remain unchanged. The count requirement never permits
invented evidence IDs.

## 4. Desktop Input and Compatibility

Desktop Nest includes `focusKeyword` in the topic-synthesis input for:

- a new topic-first research run;
- the legacy explicit “continue without reference analysis” path;
- “create more topics from this research”.

Stored-evidence regeneration uses the original source research run's focus
keyword and continues to send existing topics as duplicate exclusions.

Desktop accepts v5 as the current provider-input contract while retaining read
and recovery compatibility for persisted v3 and v4 artifacts. New calls must
use v5; old completed runs are not rewritten.

## 5. Failure and Cost Behavior

The existing bounded synthesis retry handles a provider response that violates
the exact-eight structured-output contract. If both attempts fail, the research
run fails safely and retains the bounded provider diagnostic already supported
by the research failure artifact.

The operation remains one topic-synthesis provider call in the normal case.
The current 8,000-token output ceiling and the existing preflight estimate
remain unchanged; actual output usage may rise because more topics are
returned.

## 6. Verification

Web API tests prove:

- topic synthesis advertises v5;
- the prompt requires exactly eight meaningfully distinct topics;
- focus-keyword relevance and unsupported-padding prohibitions are explicit;
- the schema and manual validator reject seven or nine topics and accept eight.

Desktop Nest tests prove:

- new research and stored-evidence regeneration forward the correct focus
  keyword into topic synthesis;
- the response projector rejects fewer or more than eight topics;
- v5 is accepted for new calls while v3 and v4 persisted contracts remain
  readable;
- existing topic grounding and duplicate-exclusion tests remain green.

No paid provider call is part of automated verification.
