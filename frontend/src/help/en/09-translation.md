# Translation

## What translation produces

Translation generates a parallel set of utterances in your chosen target language, aligned one-to-one with the source. Every source utterance maps to a translated utterance at the same position. The source transcript is not replaced — translation adds a second view accessible via the view switcher in the **Subtitle Editor**. Once produced, the translation is saved and persists across sessions.

## Choosing a target language

Select the target language from the dropdown before running translation. The list of supported languages depends on your configured LLM provider. For best quality, choose a well-supported language. Less common languages may produce acceptable but uneven results depending on the model.

## Manual vs bundle

You can trigger translation manually from the detail view at any time after transcription is complete. Alternatively, include a target language in a bundle configuration to have translation run automatically as part of the pipeline. In a bundle, translation runs after refinement and analysis, so downstream translation sees the full cleaned text. See **Refinement** for more on how pipeline steps compose.
