# Transcription Settings

## Speaker diarization

Diarization detects who spoke when and tags each utterance with a label like SPEAKER_00, SPEAKER_01, and so on. Turn it on for multi-speaker recordings and off for single-speaker content to save processing time. You can optionally set minimum and maximum speaker counts to guide detection. Diarization adds noticeable processing time. Once the transcription is ready, rename speakers to real names via the **Speaker Mapping** feature.

## Model and quality

Which Whisper models are available depends on how your deployment is configured.

**If only one model is configured**, the settings panel shows a read-only **Model** field naming it (for example `large-v3-turbo`). There is nothing to choose — every transcription uses that model.

**If several are configured**, the field is a **Quality** dropdown. Each entry shows a tier name and the model behind it:

| Tier | Speed | Notes |
|---|---|---|
| Draft (tiny) | Fastest | Good for quick previews of long files |
| Standard (base) | Fast | — |
| Good (small) | Medium | — |
| Better (medium) | Slow | — |
| Balanced (large-v3-turbo) | Fast/accurate | Recommended default |
| Best quality (large-v3) | Slowest | Maximum accuracy |

Only the tiers your deployment offers appear. The steps are not evenly spaced — the jump up to `large-v3-turbo` is large, while the gap between `large-v3-turbo` and `large-v3` is small.

## Advanced options

**Initial prompt** lets you give the model a short context sentence — useful for technical topics, proper nouns, or expected vocabulary. **Hotwords** is a comma-separated list of domain-specific terms the model should favour. Use both options sparingly; over-specifying can introduce errors.

## Presets

Save your current settings as a named preset to reuse them without reconfiguring every time. Create and manage presets on the **Presets** page.
