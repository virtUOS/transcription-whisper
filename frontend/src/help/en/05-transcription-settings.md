# Transcription Settings

## Speaker diarization

Diarization detects who spoke when and tags each utterance with a label like SPEAKER_00, SPEAKER_01, and so on. Turn it on for multi-speaker recordings and off for single-speaker content to save processing time. You can optionally set minimum and maximum speaker counts to guide detection. Diarization adds noticeable processing time. Once the transcription is ready, rename speakers to real names via the **Speaker Mapping** feature.

## Quality selection

| Tier | Speed | Notes |
|---|---|---|
| Draft | Fastest | Good for quick previews of long files |
| Standard | Fast | — |
| Good | Medium | — |
| Better | Slow | — |
| Best (fast) | Fast/accurate | Recommended default |
| Best | Slowest | Maximum accuracy |

**Best (fast)** is usually the right choice for most use cases.

## Advanced options

**Initial prompt** lets you give the model a short context sentence — useful for technical topics, proper nouns, or expected vocabulary. **Hotwords** is a comma-separated list of domain-specific terms the model should favour. Use both options sparingly; over-specifying can introduce errors.

## Presets

Save your current settings as a named preset to reuse them without reconfiguring every time. Create and manage presets on the **Presets** page.
