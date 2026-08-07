# Shortform Director Research and Shorts Analysis Follow-ups

Date: 2026-08-04
Status: Deferred; not part of the current implementation

This file records intentionally deferred ideas from the topic-first research and
UI redesign. None of these items should be implemented as a prerequisite for
the approved current design.

## 1. Separate `쇼츠 분석` Plugin

Revisit a dedicated `쇼츠 분석` or `쇼츠 정밀 분석` plugin that reuses the
existing reference-video analysis pipeline without coupling it to topic
discovery.

Potential reusable capabilities:

- verified public YouTube Shorts input;
- local media preprocessing;
- local STT;
- frame and cut extraction;
- YouTube comment collection;
- Gemini full-video analysis;
- hook and scroll-stopper analysis;
- retention mechanics;
- timestamped structure;
- pacing;
- on-screen text;
- video-claim extraction;
- reusable production patterns;
- prohibited-copy guidance;
- provider usage and calculated-cost records.

Potential product uses:

- inspect one Short in depth;
- compare several Shorts;
- extract reusable production patterns;
- save useful patterns into a future formula catalog;
- review the evidence frames and transcript behind each conclusion.

Before implementation, design the plugin as an independent workflow with its
own navigation, storage ownership, cost preflight, result history, and
comparison UX. Do not reintroduce it as a required step in idea research.

## 2. Optional Audience-Question Enrichment

After a user selects a topic, a future optional action may analyze comments from
several topically relevant videos to find recurring audience questions.

Constraints:

- do not run during default idea research;
- do not use a single style-reference video's comments as representative
  audience evidence;
- aggregate repeated questions across multiple relevant videos;
- treat comments as audience-interest signals, not factual evidence;
- keep the step optional and separately costed;
- preserve the original market evidence as the source of factual claims.

A possible user-facing action is `시청자 궁금증 더 찾기`, but its exact UI is
not decided.

## 3. Reusable Video-Formula Catalog

Revisit a formula catalog only if autonomous candidate generation proves too
inconsistent or users need repeatable branded formats.

Possible formula examples:

- misconception correction;
- problem → cause → solution;
- before/after comparison;
- listicle;
- experiment or verification;
- news briefing;
- narrative story.

A future hybrid may combine:

- built-in curated formulas;
- formulas extracted by the separate Shorts-analysis plugin;
- LLM-proposed one-off formats.

The catalog should not constrain topic discovery. Formula selection belongs
after a topic is chosen and before or during candidate generation.

## 4. Revisit Triggers

Revisit these follow-ups only when at least one is true:

- users explicitly want to analyze Shorts independently of idea research;
- autonomous formats repeat too often or vary too unpredictably;
- users request reusable brand-specific formats;
- topic cards are useful but users lack evidence about recurring audience
  questions;
- there is implementation capacity for a separately preflighted optional
  enrichment workflow.
