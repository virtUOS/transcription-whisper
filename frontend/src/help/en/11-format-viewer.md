# Format Viewer

## The four formats

Next to **Subtitles**, the detail view has the tabs **SRT**, **VTT**, **JSON** and **TXT**. Each shows the transcript in that format. transkribierBAR creates it in your browser from the current text.

- **SRT:** numbered entries with times such as `00:01:30,250 --> 00:01:34,000`, preceded by the speaker's name in square brackets: `[Name]: Text`.
- **VTT:** starts with `WEBVTT` and has times with a full stop instead of a comma (`00:01:30.250`). The names are in square brackets as in SRT.
- **JSON:** a list with `start`, `end`, `text` and `speaker` for each utterance. Start and end are milliseconds.
- **TXT:** one line per utterance without times, in the form `Name: Text`.

Utterances without a speaker appear without a name.

## Downloading

The tab shows a preview that you cannot change. The same button appears above and below the preview, for example **Download SRT**. It saves the file under the recording's name without its extension plus the file extension of the format, such as `Lecture.srt`. If the name is missing, the file is called `transcription.srt`.

## What the format contains

The format shows the state you see in the editor, including unsaved changes. Names from **Speaker Names** are filled in in all four formats; in the **Refined** view and in a translation made from it, the names from the time of the refinement apply.

Which version appears depends on the view you last chose in the **Subtitles** tab: **Original**, **Refined** or **Translated**. If **Refined** is chosen, the JSON format contains both versions in one object: `utterances` for the original and `refined_utterances` for the refined version.

## Which format fits?

| Goal | Format |
|---|---|
| Add subtitles to a video | SRT or VTT |
| Process the transcript with a program | JSON |
| Read or pass on the transcript | TXT |
