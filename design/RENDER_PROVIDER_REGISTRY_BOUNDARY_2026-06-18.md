# Render Provider Registry Boundary

Date: 2026-06-18

## Goal

Keep `VideoRenderProviderRegistry` as the render recipe provider resolver used by Template Builder sample render, while preventing it from being confused with the removed generic project render-job API.

## Design

- The removed path is the persisted generic project render-job API and store:
  `/projects/:projectId/.../render-jobs`, `VideoRenderJobsService`, and `VideoRenderJobRepository`.
- The retained path is render recipe execution provider resolution:
  `TemplateBuilderSampleRenderService` asks `VideoRenderProviderRegistry` for a provider and invokes `provider.render(...)` directly for sample renders.
- No new project render-job persistence or public endpoint should be introduced.
- The registry remains in `project-manifest` because render providers are still shared render-recipe infrastructure.

## Verification

- Add/keep a contract test that a Template Builder sample render resolves through the provider registry with the template-aware provider id.
- Keep the existing contract test that persisted video render job service exports are absent.
- Run NestJS build and the render/provider related test set.
