# Speaker Mapping

## Opening the dialog

Open the speaker mapping dialog from the **Speaker Names** button in the tab bar, or by clicking any speaker label directly in the editor. The dialog is only available when diarization has produced speaker labels for the recording.

## Renaming speakers

Each detected speaker — SPEAKER_00, SPEAKER_01, and so on — has an input field where you can enter a display name. Once saved, the display name replaces the generic label everywhere: in the editor, in all export formats, and in the refined and translated views. Leave a field blank to keep the original generic label for that speaker.

## Re-assigning utterances

If diarization misattributed an utterance to the wrong speaker, you can re-assign it from the editor without touching the rest of the transcript. Re-assignment is per-utterance. A good workflow is to rename your speakers first so labels are meaningful, then go through any misattributed utterances and reassign them to the correct speaker.

## How mappings are saved

Mappings are saved server-side and persist across sessions. Reloading the page or opening the transcript later will show the same display names. All download formats use the mapped names rather than the raw ASR labels.
