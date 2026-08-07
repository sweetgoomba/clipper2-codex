# Candidate Return Cleanup And Clipper Main Title Implementation Plan

**Goal:** Remove the failed candidate scroll restoration and make the default
Full Clipper template render a visible generated main title.

**Architecture:** Preserve route-based candidate selection, but remove all
custom scroll state. Reuse the storyboard title at the Director-to-Shortform
adapter boundary, split it into template-safe lines, and make the Python plugin
resolve the NestJS-bundled font and gradient assets in development and
packaged runtimes.

## Task 1: Remove custom candidate scroll restoration

**Files:**

- Delete:
  `src/features/shortform-director/services/shortform-director-candidate-return.service.ts`
- Delete:
  `src/features/shortform-director/services/shortform-director-candidate-return.service.spec.ts`
- Modify:
  `src/features/shortform-director/pages/candidates-page/candidates-page.component.ts`
- Modify:
  `src/features/shortform-director/pages/candidates-page/candidates-page.component.spec.ts`

1. Remove scroll-specific test setup and expectations.
2. Delete the service and lifecycle/DOM scroll code.
3. Keep storyboard navigation query parameters intact.
4. Run the candidate page and navigation tests.

## Task 2: Generate Clipper main-title lines

**Files:**

- Modify:
  `../clipper_nestjs/test/shortform-director-clipper-render-adapter.test.js`
- Modify:
  `../clipper_nestjs/src/modules/shortform-director/application/shortform-director-clipper-render.adapter.ts`

1. Add a failing assertion for balanced `mainTitle1` and `mainTitle2`.
2. Add a small deterministic title-line splitter.
3. Apply it only in `clipper-template` mode.
4. Run the adapter test.

## Task 3: Resolve the Full template font and gradient

**Files:**

- Modify:
  `../clipper_python/tests/test_template_builder_text_renderer.py`
- Modify:
  `../clipper_python/plugins/clipper_video_render/clipper_video_render/template_builder_text_renderer.py`
- Modify:
  `../clipper_electron/test/plugin-process-packaged-paths.test.js`
- Modify:
  `../clipper_electron/src/main/plugin/plugin-process.ts`
- Modify:
  `../clipper_nestjs/src/modules/plugins/infrastructure/local-plugin-process.ts`

1. Add a failing Jalnan logical-URI font-resolution test.
2. Generalize bundled template font URI resolution.
3. Add failing launch-context assertions for font and asset roots.
4. Pass source/packaged NestJS resource directories to the Python plugin.
5. Run the Python and Electron targeted tests.

## Task 4: Prevent title clipping

**Files:**

- Modify:
  `../clipper_nestjs/test/template-builder-full-family.test.js`
- Modify:
  `../clipper_nestjs/src/modules/template-builder/domain/template-builder-full-family.ts`

1. Add a failing assertion that Full-template main-title layers can contain the
   configured 80px font.
2. Set both main-title layer heights to the legacy line spacing.
3. Run the Full-template test.

## Task 5: Verify the integrated change

1. Run the relevant Angular tests without a packaged app build.
2. Run the NestJS build and targeted Node tests.
3. Run the Python targeted tests.
4. Run the Electron TypeScript build and targeted Node tests.
5. Inspect the final diffs and confirm no unrelated work was overwritten.
