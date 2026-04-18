# Analysis

## What analysis does

Analysis sends your transcript to a language model to produce a higher-level artifact — a summary, a structured protocol, chapter markers, or anything else you ask for. It does not modify the transcript. The original utterances remain unchanged regardless of what the analysis produces.

## Built-in templates

Three templates are available out of the box:

- **General summary** — a concise overview of the recording content
- **Meeting protocol** — structured output with participants, decisions, and action items
- **Chapter markers** — time-coded sections with titles, useful for long recordings

Pick the template that matches the nature of your content.

## Custom prompts

Instead of a template, write your own prompt. The model receives the full transcript text plus your prompt and returns whatever you ask for. Keep prompts direct and concrete. Avoid asking for information the transcript does not contain — the model will fill in gaps with guesses if pushed.

## Chapter hints and agenda

For long recordings with a known agenda, paste the agenda into the chapter hints field (one topic per line). The model uses this as context to produce more accurate chapter markers and to map discussion to the right agenda items.

## Running multiple analyses

You can run analysis as many times as you like, with different templates or prompts. Each result is saved separately and displayed in the analysis history. From there you can compare outputs, delete older results, or re-run any configuration.

## Source: original or refined

If a refinement exists, the analyze form shows a **Source** toggle (Original / Refined) — defaulted to **Refined**, so the LLM sees the cleaned-up text by default. Switch to **Original** to analyze the raw ASR output instead. Each stored analysis shows which source it used ("from refined" / "from original"); if the source has since changed or the refinement was deleted, the label turns amber and you can re-run to regenerate.
