import os
import requests
import torch
import torchaudio
import argparse
import time
from pyannote.audio import Pipeline
from pydub import AudioSegment
from urllib.parse import urlparse

def download_audio(url: str, output_folder: str = "downloads") -> str:
    os.makedirs(output_folder, exist_ok=True)
    parsed = urlparse(url)
    filename = os.path.basename(parsed.path) or "audio.mp3"
    filepath = os.path.join(output_folder, filename)

    # print(f"Downloading {url}...")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(filepath, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"Saved to {filepath}")

    #filepath = url
    return filepath

def convert_to_wav(mp3_path: str) -> str:
    audio = AudioSegment.from_file(mp3_path)
    wav_path = mp3_path.rsplit(".", 1)[0] + ".wav"
    audio.export(wav_path, format="wav")
    return wav_path

def truncate_float(time: float) -> float:
    """Truncate time to 1 decimal place."""
    return float(f"{time:.1f}")

def create_segments(diarization) -> list[dict]:
    """Create segments from diarization output."""
    segments = []
    idx = 0
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        duration = turn.end - turn.start
        segments.append({
            "segment_id": str(idx),
            "speaker_id": speaker,
            "start_time": truncate_float(turn.start),
            "end_time": truncate_float(turn.end),
            "duration_sec": truncate_float(duration)
        })
        idx += 1
    return segments

def consolidate_segments(segments: list[dict]) -> list[dict]:
    """Consolidate segments with the same speaker."""
    if not segments:
        return []

    consolidated = []
    prev = segments[0].copy()
    for seg in segments[1:]:
        if seg['speaker_id'] == prev['speaker_id']:
            # Extend the previous segment
            prev['end_time'] = seg['end_time']
            prev['duration_sec'] = truncate_float(prev['end_time'] - prev['start_time'])
        else:
            consolidated.append(prev)
            prev = seg.copy()
    consolidated.append(prev)
    return consolidated

def diarize_audio(wav_path: str) -> list[dict]:
    print(f"Diarizing audio file: {wav_path}")
    start_time = time.time()
    waveform, sample_rate = torchaudio.load(wav_path)
    
    pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", use_auth_token=os.getenv("HUGGINGFACE_TOKEN"))
    pipeline.to(torch.device("cuda"))
    diarization = pipeline({"waveform": waveform, "sample_rate": sample_rate})
    print(f"Diarization completed in {time.time() - start_time:.2f} seconds")

    print("\n--- Speaker Segments ---")
    segments = create_segments(diarization)
    if not segments:
        return []
    
    consolidated = consolidate_segments(segments)
    return consolidated

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio_url", required=True, help="URL of the audio file to diarize")
    args = parser.parse_args()
    audio_url = args.audio_url
    downloaded_path = download_audio(audio_url)
    wav_path = convert_to_wav(downloaded_path)
    diarize_audio(wav_path)

# 1 min wav file
# CPU: 44.43 seconds
# GPU: 5.30 seconds

# speaker id
# start_time = 0.0s
# end_time = 471.0s
# duration = 471.0s

# --- Speaker Segments ---
# SPEAKER_01: 0.0s - 4.7s (4.7s)
# SPEAKER_02: 4.7s - 20.0s (15.3s)
# SPEAKER_01: 20.3s - 29.0s (8.7s)
# SPEAKER_00: 29.0s - 30.2s (1.1s)
# SPEAKER_00: 30.6s - 49.8s (19.1s)
# SPEAKER_00: 55.0s - 62.0s (7.0s)
# SPEAKER_01: 62.0s - 68.2s (6.2s)
# SPEAKER_00: 63.4s - 63.9s (0.4s)
# SPEAKER_01: 68.5s - 68.5s (0.0s)
# SPEAKER_00: 68.5s - 111.4s (42.9s)
# SPEAKER_01: 111.6s - 111.7s (0.1s)
# SPEAKER_00: 111.7s - 114.8s (3.1s)
# SPEAKER_01: 114.8s - 114.8s (0.0s)
# SPEAKER_00: 115.5s - 133.2s (17.7s)
# SPEAKER_01: 133.2s - 138.8s (5.6s)
# SPEAKER_00: 134.1s - 134.7s (0.6s)
# SPEAKER_00: 139.3s - 155.1s (15.8s)
# SPEAKER_01: 155.1s - 157.7s (2.6s)
# SPEAKER_00: 158.5s - 180.6s (22.1s)
# SPEAKER_00: 181.9s - 188.8s (7.0s)
# SPEAKER_00: 188.9s - 195.0s (6.0s)
# SPEAKER_03: 195.3s - 197.9s (2.6s)
# SPEAKER_00: 198.5s - 213.0s (14.5s)
# SPEAKER_01: 212.9s - 218.1s (5.2s)
# SPEAKER_02: 226.8s - 232.2s (5.4s)
# SPEAKER_01: 232.6s - 240.0s (7.5s)
# SPEAKER_02: 240.1s - 246.1s (6.0s)
# SPEAKER_04: 246.6s - 255.0s (8.3s)
# SPEAKER_04: 255.2s - 282.2s (27.0s)
# SPEAKER_02: 282.4s - 287.6s (5.2s)
# SPEAKER_04: 287.8s - 347.2s (59.4s)
# SPEAKER_04: 347.5s - 350.2s (2.6s)
# SPEAKER_04: 350.7s - 383.2s (32.6s)
# SPEAKER_02: 383.4s - 385.0s (1.6s)
# SPEAKER_04: 385.0s - 413.7s (28.8s)
# SPEAKER_02: 414.0s - 414.0s (0.0s)
# SPEAKER_04: 414.0s - 436.6s (22.6s)
# SPEAKER_02: 437.0s - 439.6s (2.6s)
# SPEAKER_04: 439.7s - 440.2s (0.4s)
# SPEAKER_02: 450.2s - 455.0s (4.8s)
# SPEAKER_01: 455.0s - 455.1s (0.1s)
# SPEAKER_02: 455.1s - 455.2s (0.1s)
# SPEAKER_01: 455.2s - 455.2s (0.0s)
# SPEAKER_01: 455.3s - 460.0s (4.7s)
# SPEAKER_01: 460.2s - 461.2s (1.0s)
# SPEAKER_01: 461.3s - 463.0s (1.7s)
# SPEAKER_01: 463.0s - 471.0s (7.9s)
# SPEAKER_02: 471.0s - 485.0s (14.0s)
# SPEAKER_03: 485.6s - 509.0s (23.3s)
# SPEAKER_02: 509.0s - 520.7s (11.7s)
# SPEAKER_03: 521.4s - 559.9s (38.5s)
# SPEAKER_02: 560.0s - 578.7s (18.7s)
# SPEAKER_02: 579.7s - 579.7s (0.0s)
# SPEAKER_03: 579.7s - 629.0s (49.3s)
# SPEAKER_02: 629.0s - 629.6s (0.7s)
# SPEAKER_03: 630.4s - 658.0s (27.5s)
# SPEAKER_02: 658.0s - 660.3s (2.4s)