# Shortform Director AI-Generated Visual Content Design

## 1. Objective

Shortform Director must let the selected AI video model generate all
scene-native visual content, including exact numbers, chart-like graphics,
names, logos, labels, and other visible text. The system accepts that generated
text or factual-looking graphics can be distorted.

In `clipper-template` mode, Clipper remains responsible only for narration TTS
and the subtitle that follows that spoken narration. Clipper must not add a
separate data chart, metric, timeline, or informational text overlay.

## 2. Scope

This change applies to newly generated storyboards and their AI video prompts.
It does not rewrite an already stored storyboard or regenerate an existing
provider asset.

The change does not:

- add another LLM call or change the existing two-call cost approval;
- change the selected AI video provider or model constraints;
- remove Clipper narration TTS or its spoken-word subtitle;
- promise that AI-generated text, logos, charts, or likenesses are accurate.

## 3. Storyboard Media Policy

Every scene continues to use:

- `baseMedium: generated-video`;
- `overlayMode: none`;
- `searchBrief: null`;
- `programmaticBrief: null`.

The scene-media decision must write a concrete `generationBrief` that directly
visualizes the scene. It may and, when relevant, should request:

- exact strings from `scene.onScreenText`;
- numerical claims such as `1주 → 3주 → 5주` and `톱50`;
- chart, ranking, timeline, dashboard, headline, sign, and interface graphics;
- named artists, products, platforms, logos, album art, and recognizable
  subject matter;
- scene-specific actions, environments, camera movement, and visual
  progression.

Generated text and data graphics are allowed even when they may render
incorrectly. The prompt must not replace relevant subject matter with a vague
metaphor merely because the scene has factual risk.

Adjacent scenes must not reuse the same abstract motif as their main visual.
Waves, light streaks, particles, silhouettes, and similar abstraction are
allowed only when the scene itself calls for them, not as a generic fallback.

## 4. Audio and Subtitle Boundary

For `clipper-template` mode:

- the generated clip must not contain narration or dialogue;
- the generated clip must not create subtitles synchronized to the spoken
  narration;
- the generated clip may contain scene-native visible text, numbers, charts,
  labels, signs, logos, and interface graphics;
- the generated clip may contain ambient sound effects;
- Clipper produces narration TTS and its spoken-word subtitle;
- Clipper does not produce a separate informational overlay from
  `scene.onScreenText`.

Accordingly, `audioPolicy.captions: false` means that the provider must not
generate spoken-word subtitles. It does not prohibit visible text that belongs
to the scene or its data visualization.

## 5. Prompt Contract

The `scene-media-decision` system prompt must:

1. keep generated video as the only base medium;
2. explicitly allow exact visible text and factual-looking graphics;
3. instruct the model to include relevant `scene.onScreenText` in the generated
   video itself;
4. distinguish spoken-word subtitles from scene-native text;
5. require concrete, scene-specific subjects and actions;
6. reject abstract visual substitution caused only by factual-risk concerns;
7. require visual variation across scenes;
8. stop describing generated video as incapable of showing factual subject
   matter.

The output schema and maximum call count remain unchanged.

## 6. Compilation and Rendering

The deterministic compiler continues to store the generated-video brief as the
visual layer requirement. It must not create a programmatic data diagram or
timeline from `scene.onScreenText`.

Narration text continues through the narration cue and TTS pipeline. The final
Clipper render may display the spoken narration subtitle, but informational
copy intended for the scene must be part of the AI-generated video pixels.

## 7. Validation and Tests

Regression coverage must prove that:

- the scene-media system prompt allows numbers, charts, logos, names, and
  scene-native text;
- `captions: false` forbids spoken-word subtitles but not scene-native text;
- the prompt requires exact `onScreenText` to be requested inside the generated
  video;
- the prompt requires concrete and varied visuals instead of repeated generic
  abstraction;
- the existing output schema, two-call limit, generated-video base medium, and
  Clipper TTS boundary remain intact;
- no programmatic diagram or informational overlay is introduced.

Provider calls are not needed for automated verification. Visual quality must
be smoke-tested by generating a new storyboard and inspecting its per-scene
generation briefs before paying for video generation.
