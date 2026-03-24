from app.models import Utterance


def _format_srt_timestamp(ms: int) -> str:
    s, ms_rem = divmod(ms, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(ms_rem):03d}"


def _format_vtt_timestamp(ms: int) -> str:
    s, ms_rem = divmod(ms, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d}.{int(ms_rem):03d}"


def _apply_speaker(text: str, speaker: str | None, mappings: dict[str, str] | None = None) -> str:
    if not speaker:
        return text
    name = mappings.get(speaker, speaker) if mappings else speaker
    return f"[{name}]: {text}"


def generate_srt(utterances: list[Utterance], speaker_mappings: dict[str, str] | None = None) -> str:
    lines = []
    for i, utt in enumerate(utterances, 1):
        start = _format_srt_timestamp(utt.start)
        end = _format_srt_timestamp(utt.end)
        text = _apply_speaker(utt.text, utt.speaker, speaker_mappings)
        lines.append(f"{i}\n{start} --> {end}\n{text}\n")
    return "\n".join(lines)


def generate_vtt(utterances: list[Utterance], speaker_mappings: dict[str, str] | None = None) -> str:
    lines = ["WEBVTT\n"]
    for utt in utterances:
        start = _format_vtt_timestamp(utt.start)
        end = _format_vtt_timestamp(utt.end)
        text = _apply_speaker(utt.text, utt.speaker, speaker_mappings)
        lines.append(f"{start} --> {end}\n{text}\n")
    return "\n".join(lines)


def generate_txt(utterances: list[Utterance], speaker_mappings: dict[str, str] | None = None) -> str:
    lines = []
    for utt in utterances:
        lines.append(_apply_speaker(utt.text, utt.speaker, speaker_mappings))
    return "\n".join(lines)
