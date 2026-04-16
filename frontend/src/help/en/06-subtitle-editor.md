# Subtitle Editor

## Editing text

Click on any utterance text to make it editable. Changes are held locally until you save — you can edit multiple utterances before committing anything. To remove an utterance, clear its text and save. Long utterances can be split at the cursor position using the split action that appears in the toolbar while editing.

## Timestamps and the media player

The media player at the top of the detail view stays in sync with the editor. Clicking an utterance seeks the player to that position. While playing, the current utterance is highlighted automatically. Timestamps come directly from the ASR output and are read-only — adjust them by re-running transcription with different settings if needed.

## Saving your edits

Edits are not saved automatically. An unsaved-changes indicator appears when you have local modifications. If you try to navigate away, a confirmation dialog will ask you to confirm or discard. Once saved, the updated text is used in all downloads — SRT, VTT, plain text, and any other export format.

## Original, refined, and translated views

The view switcher above the editor lets you toggle between the original transcript, a refined version, and a translated version (if those have been produced). Edits apply only to the currently active view. Editing the original does not affect the refined view, and vice versa. See **Refinement** and **Translation** for details on those views.
