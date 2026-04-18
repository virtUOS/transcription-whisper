# Translation

## What translation produces

Translation generates a parallel set of utterances in your chosen target language, aligned one-to-one with the source. Every source utterance maps to a translated utterance at the same position. The source transcript is not replaced — translation adds a second view accessible via the view switcher in the **Subtitle Editor**. Once produced, the translation is saved and persists across sessions.

## Choosing a target language

Select the target language from the dropdown before running translation. The list of supported languages depends on your configured LLM provider. For best quality, choose a well-supported language. Less common languages may produce acceptable but uneven results depending on the model.

## Manual vs bundle

You can trigger translation manually from the detail view at any time after transcription is complete. Alternatively, include a target language in a bundle configuration to have translation run automatically after transcription finishes.

## Choosing the source

If a refinement exists, the translate modal shows a **Source** toggle (Original / Refined) — defaulted to **Refined**, so by default the translator sees the cleaned-up text. Switch to **Original** to translate the raw ASR output instead. Without a refinement the toggle is hidden and the original is always used. The view switcher labels each translation with its source, e.g. `Translated (EN · from refined)`.

If you later edit the original transcript, or delete the refinement that a translation was made from, the view switcher shows a small amber hint ("source has newer content" or "source no longer available"). Click it to re-open the translate modal and re-run.

See **Bundles** for how pipeline steps are sequenced.
