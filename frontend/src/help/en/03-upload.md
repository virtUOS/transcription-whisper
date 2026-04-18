# Upload

## Supported formats

The app accepts MP3, WAV, MP4, WebM, M4A, MOV, AAC, Opus, and OGG files up to 1 GB. Drag a file onto the upload area or click to open the file browser.

## Choosing a language

Use **Auto-detect** when you are unsure of the language. Detection adds a small overhead, so if you know the language in advance, selecting it manually gives faster results and slightly better accuracy.

## Choosing an ASR backend

**MurmurAI** is a remote service — it processes files quickly and handles longer recordings well. Choose it when turnaround time matters.

**WhisperX** runs locally and provides fine-grained speaker diarization, giving more precise timestamps and cleaner speaker segments. Choose it when accurate speaker separation is more important than speed.

Only the backends your administrator has enabled appear in the interface.

## Using a bundle

A bundle chains transcription, refinement, analysis, and translation presets into a single configuration. Select one from the bundle dropdown before starting to run all configured stages automatically after transcription finishes. You can create and manage bundles on the **Presets** page. See **Bundles** for how the pipeline composes.
