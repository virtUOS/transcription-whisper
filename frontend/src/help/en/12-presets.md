# Presets

## What presets are

A preset saves settings under a name, so you do not have to enter them again for every recording. There are presets for transcription, for analysis and for refinement. Presets belong to your account, and only you see them.

You use them in three places:

- **Transcription:** in the **Presets** group of the **Upload** and **Record** views, in the **Transcription** field. The section "Transcription Settings" explains it.
- **Analysis:** in the **Analysis** field of the analysis form.
- **Refinement:** at the top of the dialog for refining.

Next to each of these fields is **Save as preset**. Enter a name there and confirm with the check mark or Enter. transkribierBAR saves the current settings under that name. The cross or Esc cancels.

## The Presets page

Click **Presets** in the header. The page **My Presets** has four tabs: **Transcription**, **Analysis**, **Refinement** and **Bundles**. The section "Bundles" explains the last one.

Each tab lists your saved entries with **Edit** and **Delete**. **+ New preset** opens a form with a **Name** and the fields of the preset type. **Save** stays unavailable until you have entered a name. **Cancel** closes the form.

**Delete** asks for confirmation: **Delete this preset? Bundles using it will lose the reference.** Only the preset is removed. Bundles that used it remain, but without that part. Transcriptions that already exist are not affected.

## Transcription presets

A transcription preset stores language, speaker detection, initial prompt, hotwords and model. The form on the Presets page has the fields **Name**, **Transcription language**, **Model**, **Hotwords** and **Initial prompt**. The model is fixed to {{default_model}} and cannot be changed.

If you choose such a preset in **Upload** or **Record**, it applies language, speakers, initial prompt and hotwords. The model stays {{default_model}}.

> **Speakers.** The Presets page has no field for speaker detection. If you edit a transcription preset there, speaker detection in this preset is switched off. If you want to change speaker settings, set them in **Upload** or **Record** and save a new preset with **Save as preset**.

## Analysis presets

An analysis preset stores the template and the output language. For **Custom** it also stores your own instruction. The form on the Presets page has the fields **Name**, **Select a template**, **Output language** and, for **Custom**, **Customize prompt**.

If you save a preset in the analysis form with **Save as preset**, it also stores the chapters and the agenda you entered there. Choosing the preset fills them back in. The section "Analysis" explains the form.

> **Chapters and agenda.** The Presets page has no fields for chapters and agenda. If you edit an analysis preset there, they are removed from the preset.

## Refinement presets

A refinement preset stores only a context text, for example a note on the topic and on technical terms. The form on the Presets page has the fields **Name** and **Context (optional)**. The section "Refinement" explains what the context does.
