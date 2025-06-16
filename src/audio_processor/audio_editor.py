from pydub import AudioSegment
import tempfile

def extract_segment(audio_path: str, start_sec: float, end_sec: float, type: str) -> str:
    """Extracts a segment and returns a temporary audio file path."""
    audio = AudioSegment.from_file(audio_path)
    if start_sec != None and end_sec != None:
        segment = audio[start_sec * 1000:end_sec * 1000]  # milliseconds
        tmp_audio = tempfile.NamedTemporaryFile(suffix=f".{type}", delete=False)
        segment.export(tmp_audio.name, format=f"{type}")
        return tmp_audio.name
    return audio_path

def convert_type(path: str, to_type: str) -> str:
    audio = AudioSegment.from_file(path)
    audio_path = path.rsplit(".", 1)[0] + f".{to_type}"
    audio.export(audio_path, format=f"{to_type}")
    return audio_path