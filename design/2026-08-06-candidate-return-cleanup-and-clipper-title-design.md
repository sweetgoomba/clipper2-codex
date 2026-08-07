# Candidate Return Cleanup And Clipper Main Title Design

## Problems

1. The custom candidate-page scroll restoration has failed repeatedly. It
   stores the shell scroll offset in history state and restores it from
   `AfterViewChecked`, but the returned page still starts at the top.
2. A Shortform Director final render made with the Clipper template shows
   captions but no usable main title.

The second problem has three concrete causes:

- the Director render adapter sends the complete storyboard title only as
  `mainTitle1` and never supplies `mainTitle2`;
- the packaged Python renderer cannot resolve the Full template's
  `JalnanGothic.otf` URI to the font bundled with the NestJS resources;
- the packaged renderer cannot resolve the Full template's gradient URI, so
  the title also loses its intended background.

## Expected Behavior

- No custom candidate scroll offset is stored or restored.
- Returning from the storyboard still targets the correct candidate page,
  including its profile, research run, and topic selection.
- Clipper-template final renders use the storyboard's generated title as a
  visible, balanced one- or two-line main title.
- The Full template's Jalnan font and gradient resolve in both source and
  packaged runtimes.
- AI-integrated renders continue to omit Clipper title overlays.

## Design

### Candidate return

Delete `ShortformDirectorCandidateReturnService` and its test. Remove the
service injection, `AfterViewChecked` restoration, scroll viewport lookup, and
offset recording from `CandidatesPageComponent`.

Keep the candidate route query parameters and `NavHistoryService` fallback
navigation. Those changes restore the correct page selection and are
independent of the failed scroll restoration.

### Main title content

In `ShortformDirectorClipperRenderAdapter`, normalize the already
LLM-generated storyboard title and split it near its visual midpoint. Prefer a
word or punctuation boundary and keep each line within the Full template's
usable width. Use `mainTitle1` only for a short title and both
`mainTitle1`/`mainTitle2` for a longer title.

This does not add an inference request or change persisted storyboard schemas,
so existing storyboards gain a title when rendered again.

### Template assets

Teach the Python text renderer to resolve every
`template-builder/fonts/<file>` URI from the configured bundled font
directory, not only Pretendard.

Pass the NestJS template font directory and legacy Full-template asset
directory into the Python plugin in source and packaged launch modes. The
existing visual asset resolver can then map the logical gradient URI to
`clipper-studio-seed/template/gradient.png`.

Increase the Full template main-title layer height to accommodate its 80px
Jalnan font without vertical clipping.

## Verification

- Angular candidate-page tests no longer reference or expect custom scroll
  state, while route context and back fallback tests stay green.
- NestJS adapter tests assert balanced `mainTitle1` and `mainTitle2` for a long
  title and no title overlays in AI-integrated mode.
- Python tests prove the Jalnan logical URI resolves through the configured
  bundled font directory.
- Electron launch-context tests prove source and packaged plugins receive the
  expected font and template-asset directories.
- Relevant Angular, NestJS, Python, and Electron targeted test suites pass.
