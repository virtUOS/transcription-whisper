# Transcription Settings

## Language and model

The **Transcription** group has two fields.

**Transcription language:** The default is **Auto-detect**; the speech recognition then determines the language by itself. If you know the language, choose it from the list. German, English, Spanish, French and Turkish are at the top, followed by a divider and all other languages in alphabetical order.

**Model:** The field is read-only and shows {{default_model}}. It is the only configured model, so there is nothing to choose. Every transcription uses it.

## Detecting speakers

The **Speakers** group has the switch **Detect speakers**. It is on by default and separates the contributions of different people. If only one person speaks, you can turn it off.

When the switch is on, you can narrow down the number of people: **Min speakers** (default 1) and **Max speakers** (default 2). Values from 1 to 20 are allowed. If you set the minimum above the maximum, the maximum follows, and the other way round.

You give names to the detected people after the transcription, in the **Subtitles** tab under **Speaker Names**.

## Advanced options

**Advanced options** reveals two more fields. Both are optional.

- **Initial prompt:** context for the transcription, for example the topic or proper names.
- **Hotwords:** comma-separated technical terms.

Both entries go to the speech recognition. Empty fields are not sent.

## Presets

The **Presets** group is the first group.

- **Transcription:** This selection field appears once you have saved presets. If you choose a preset there, it applies language, speakers, initial prompt and hotwords.
- **Save as preset:** Enter a name and confirm with the check mark or Enter. transkribierBAR saves the current settings under that name.
- **Bundles:** This field appears once you have created bundles. The section "Upload" explains what it does.

You manage presets on the **Presets** page in the header.

## The summary

After you click **Transcribe**, one line replaces the settings. It names the filename, the size, the model, the language (**auto** if you chose none), the speakers (**no speakers** or, for example, **1–2 speakers**) and, if used, the bundle.
