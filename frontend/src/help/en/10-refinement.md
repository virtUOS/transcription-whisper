# Refinement

## What refinement does

Refinement runs a language model cleanup pass over your transcript. It removes filler words (um, uh, you know), fixes speaker attribution errors where the wrong speaker was tagged mid-sentence, and smooths fragmented or run-on sentences into readable prose. The original transcript is fully preserved — refinement produces a separate view, not an in-place edit. It stays in the source language; it is not a translation.

## When it helps

Refinement is most useful for noisy sources: informal conversations, interviews, group discussions with crosstalk, or any recording where fillers and disfluencies are dense. It also helps when diarization made attribution mistakes across adjacent utterances. The refined transcript is often significantly more readable than the raw ASR output.

## When to skip it

For clean, single-speaker recordings — lectures, voiceovers, prepared speeches — the raw ASR output is typically already high-quality. Running refinement adds LLM cost and processing time without meaningful gain. Skip it when the original already reads well.

## How it composes with other steps

In a bundle pipeline, refinement always runs before analysis and translation. When a refinement exists, analysis and translation default to using it as input — so a bundle that includes a refinement step automatically feeds the cleaned-up text to the downstream stages. You can override this per run via the **Source** toggle in the translate and analyze modals, or skip refinement in the bundle altogether to keep downstream stages on the original. Refinement also remains usable on its own as a separate view you can read, edit, and download. See **Analysis**, **Translation**, and **Bundles** for more.
