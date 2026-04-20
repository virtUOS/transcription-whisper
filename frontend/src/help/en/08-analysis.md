# Analysis

## What analysis does

Analysis sends your transcript to a language model to produce a higher-level artifact — a summary, a structured protocol, chapter markers, or anything else you ask for. It does not modify the transcript. The original utterances remain unchanged regardless of what the analysis produces.

## Built-in templates

Three templates are available out of the box, plus a **Custom** option for your own prompt:

- **Summary with chapters** — an overall summary plus time-coded chapter breakdown, useful for long recordings
- **Meeting protocol** — structured notes with key points, decisions, and action items
- **Agenda-based notes** — notes structured around a provided meeting agenda

Pick the template that matches the nature of your content.

## Custom prompts

Select **Custom** to write your own prompt. The model receives the full transcript text plus your prompt and returns whatever you ask for. Keep prompts direct and concrete. Avoid asking for information the transcript does not contain — the model will fill in gaps with guesses if pushed.

## Chapter hints and agenda

The **Summary with chapters** template shows an optional **Define chapters** field where you can pre-declare chapter titles and descriptions (one per line) to guide segmentation. The **Agenda-based notes** template shows an **Agenda** field — paste your agenda there and the model will structure the output around those items.

## Running multiple analyses

You can run analysis as many times as you like, with different templates or prompts. Each result is saved separately and displayed in the analysis history. From there you can compare outputs, delete older results, or re-run any configuration.

## Source: original or refined

If a refinement exists, the analyze form shows a **Source** toggle (Original / Refined) — defaulted to **Refined**, so the LLM sees the cleaned-up text by default. Switch to **Original** to analyze the raw ASR output instead. Each stored analysis shows which source it used ("from refined" / "from original"); if the source has since changed or the refinement was deleted, the label turns amber and you can re-run to regenerate.
