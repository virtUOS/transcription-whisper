# Format Viewer

## The four formats

The detail view offers four export formats, each suited to different workflows:

- **SRT** — The most widely supported subtitle format. Numbered entries with `HH:MM:SS,mmm` timestamps. Works with virtually every video player and editing tool.
- **VTT** — The modern WebVTT standard designed for HTML5 video. Structurally similar to SRT but with cleaner syntax and native browser support.
- **JSON** — A structured list of utterances with start time, end time, text, and speaker label. The right choice when you want to process the transcript programmatically. When a refinement exists, the JSON export is an object with both arrays nested inside: `{ "utterances": [...], "refined_utterances": [...] }`.
- **TXT** — Plain text with speaker labels but no timestamps. Easy to read, share, or paste into a document.

## Downloading

Each format has its own tab. Click a tab to preview the content, then hit **Download** to save the file. Speaker names assigned in Speaker Mapping are reflected in all four formats.

## Which format to pick?

| Goal | Best format |
|---|---|
| Add subtitles to a video | SRT or VTT |
| Post-process programmatically | JSON |
| Read or share the transcript | TXT |
| Embed in a web player | VTT |
