# Subtitle Editor

## Editing text

Click the pencil icon next to an utterance to make its text editable — or use Tab / Shift+Tab to move between rows while editing. Changes are held locally until you save, so you can edit multiple utterances before committing anything. Esc cancels the current edit. Tab commits the current edit and jumps to the next utterance; Shift+Tab moves backward.

## Editing timestamps and speaker labels

A pencil icon next to each start and end timestamp opens an inline editor in `HH:MM:SS` format. Editing a start time cascades backward through any previous rows that would otherwise overlap; editing an end time cascades forward. Before the change is applied, a confirmation tells you how many neighboring rows would be affected.

The speaker cell has two icons: the pencil renames the speaker on this row only, and the users icon opens the Speaker Mapping dialog to rename the speaker everywhere. A colored dot marks each row's speaker — all rows belonging to the same speaker share a color.

## Row operations

Hover a row to reveal three actions in the text cell: merge-with-next combines this utterance with the one below (joining the text and extending the end time), the plus icon inserts a new empty row after this one, and the trash icon deletes the row after a confirmation. On wider screens the plus icon also appears in the row-number column.

## Searching

The search bar above the editor filters by text, speaker, or both — the **Text** and **Speaker** toggles switch the scope. Matches are highlighted, and the row immediately before and after every match is shown as context. Non-matching, non-context rows are collapsed into "… N hidden …" separators. The count beside the input shows how many utterances matched.

## Timestamps and the media player

The media player at the top of the detail view stays in sync with the editor. Clicking anywhere on a row — timestamp, speaker, or text — seeks the player to that utterance's start. While playing, the current utterance is highlighted and the editor auto-scrolls to keep it in view.

## Saving your edits

Edits are not saved automatically. When you have local modifications, an unsaved-changes indicator appears alongside **Save changes** and **Restore original**. Restore discards all local edits and reloads the stored transcript from the server. If you try to navigate away with unsaved changes, a confirmation dialog will ask you to confirm or discard. Once saved, the updated text is used in every export format — SRT, VTT, plain text, and the rest.

## Refining and translating from the editor

When an LLM is configured, the editor toolbar shows **Refine transcription** and **Translate** buttons. Each opens a small dialog — refinement takes an optional context note (savable as a preset), translation takes a target language. When a refinement exists, the translate dialog also shows a **Source** toggle so you can pick whether to translate from the refined or the original text (defaults to refined). The resulting view appears next to the original, and a view switcher lets you toggle between **Original**, **Refined**, and the translated version (labelled with its source, e.g. "from refined"). Refined and translated views are read-only; edits only apply to the original. If you later edit the original or delete the refinement a translation came from, a small amber hint appears in the toolbar so you can re-run. Use the small delete buttons next to the switcher to remove a refined or translated copy.

## Reviewing refinement changes

With the refined view active, a changes-summary banner describes what the LLM modified, names the provider and model, and shows any context you supplied. Rows the LLM changed are flagged with an amber dot and a left border — click one to expand a side-by-side comparison of the original and refined text. See **Refinement** and **Translation** for how those pipelines work.
