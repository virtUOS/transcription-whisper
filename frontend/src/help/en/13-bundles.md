# Bundles

## What a bundle is

A bundle is a named composition of pipeline stages: transcription, refinement, analysis, and translation. Each stage is optional except transcription, and each stage slot holds one preset (or a target language for translation). Selecting a bundle on the Upload or Record view means all configured stages run automatically in sequence after transcription completes — no manual triggering required.

## The pipeline

![Bundle pipeline](./assets/bundle-pipeline.svg)

Stages always execute in order: **transcription → refinement → analysis → translation**. When a refinement step is configured, analysis and translation default to reading the refined text rather than the original — so the cleaned-up output propagates forward through the pipeline. Drop the refinement step (or flip the **Source** toggle when running manually) to keep those stages on the original transcript instead.

## The default bundle and auto-run

You can mark one bundle as the default. It will be pre-selected for every new upload and recording. Once transcription finishes, the remaining stages start automatically and progress indicators show each stage's status. If an individual stage fails, you can dismiss the error and continue without re-running the whole pipeline.

## Creating and using bundles

Create bundles on the **Presets** page by picking one preset per stage and giving the bundle a name. Mark it as default if you want it applied automatically. On the Upload or Record view, switch the active bundle via the bundle dropdown at any time before submitting.

## Bundle or manual steps?

Use a bundle when you apply the same pipeline repeatedly — for example, "every meeting recording: refine, then summarize in English, then translate to German". Use manual steps for one-off recordings that need different treatment or where you want to inspect intermediate results before proceeding.
