# Refinement

## What refinement does

In refinement, a language model goes through your transcript and corrects clear errors. It is meant to change only the following:

- spelling and punctuation errors,
- obvious grammar errors that are recognition errors and not how the person actually spoke,
- inconsistent technical terms and proper names,
- hesitation sounds such as "uh", "um" or "hm",
- false starts and restarts.

The language model is not to rephrase anything, not to turn spoken language into written language, not to change times or speakers, and to return exactly as many utterances as it received. When unsure, it should leave the text as it is. Refinement is not a translation; see the "Translation" section for that.

The original stays unchanged. The refinement is a version of its own, which you view with **Refined** next to **Original**. It is saved with the transcription, is there again when you reopen it, and is deleted together with it.

> **Save first.** Refinement works with the saved text. Changes in the editor that you have not yet saved with **Save changes** are not included.

## When it is worth it

Refinement only concerns the points listed above. It is therefore worth it mainly when your transcript contains many of them, for example hesitation sounds or inconsistently spelled technical terms and names. The changes summary shows what the language model changed.

## Refining

In the **Subtitles** tab, click **Refine with LLM** above the table. The button is there as long as no refinement exists. At the top of the dialog you can choose or save a preset. In the **Context (optional)** field, give hints that help the language model with technical terms and proper names, for example "Computer science lecture, speaker is Prof. Müller". Then click **Refine**. **Cancel** closes the dialog.

The language model receives the original with the names you gave under **Speaker Names**. Assign the names before you refine. Later renames do not reach the **Refined** view.

While refinement runs, the button reads **Refining transcription...** and the context field and the buttons are locked. With more than 50 utterances, a note says the refinement may take several minutes. The page waits for the language model. Stay on it until the dialog closes. If you leave the page anyway, the refinement keeps running on the server. You see it when you reopen the transcription later. A new attempt before it has finished fails. Afterwards the editor shows the **Refined** view.

If it fails, the dialog reads **Refinement failed. Please try again.** Try again then.

## Reading the refined view

In the **Refined** view, a bar above the table shows the **Changes Summary**, with the number of changed utterances. Click it to expand or collapse. Expanded, it describes in words what the language model changed and names the **Context**, if you gave one.

Changed rows have an amber stripe on the left edge and, on larger screens, a dot next to the row number. Clicking the dot shows **Original** and **Refined** side by side (larger screens only). The view is read-only. If you want to change text yourself, do so in the original.

## If some sections could not be refined

transkribierBAR sends the utterances to the language model in sections. If a section still fails after several automatic attempts, the others are refined and saved anyway. The failed sections keep their original text. If all of them fail, no refinement is created and you see the error message.

The affected rows have a dashed gray border and, on larger screens, a hollow gray dot. The bar also says, for example, **Not refined (original text kept): utterances 451–500**. **Retry failed sections** repeats only those sections, while the button reads **Retrying…**. The saved context applies. What has already succeeded is not sent again. If a section fails again, it stays in the list.

Two messages can appear there: **Retry failed. Please try again.** and **Utterances were added or removed since this refinement was saved. Delete the refinement and refine again.**

## If you change the original

The refinement does not adapt. If you change text in the original after refining and save, **original was edited – delete and refine again** appears in amber in the toolbar. Until then the **Refined** view shows the older text. Changes to times or names do not count here.

**Delete Refinement** removes the refinement after a confirmation prompt. The original stays unchanged. Afterwards you can refine again. Analyses and translations that were made from the deleted refinement show **source no longer available**, an analysis right away, a translation once you reopen the transcription.

## How it works with other steps

Analysis and translation offer the refinement as the **Source** and choose it on their own as soon as one exists. You can switch to **Original** there.

In a bundle with a refinement preset, your browser refines automatically after the transcription, using the preset's context. Analysis and translation follow. Stay on the page until all steps are finished.
