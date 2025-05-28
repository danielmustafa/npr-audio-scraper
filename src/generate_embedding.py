from resemblyzer import VoiceEncoder, preprocess_wav
from pydub import AudioSegment
import numpy as np
import argparse
import tempfile
import os

def extract_segment(audio_path: str, start_sec: float, end_sec: float) -> str:
    """Extracts a segment and returns a temporary .wav file path."""
    audio = AudioSegment.from_file(audio_path)
    segment = audio[start_sec * 1000:end_sec * 1000]  # milliseconds
    tmp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    segment.export(tmp_wav.name, format="wav")
    return tmp_wav.name

def generate_embedding(segment_wav_path: str) -> np.ndarray:
    wav = preprocess_wav(segment_wav_path)
    encoder = VoiceEncoder()
    embedding = encoder.embed_utterance(wav)
    return embedding

def save_embedding(embedding: np.ndarray, output_path: str):
    np.save(output_path, embedding)
    print(f"Embedding saved to {output_path}.npy")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("audio_path", help="Input audio file (.wav, .mp3, etc.)")
    parser.add_argument("start", type=float, help="Start time in seconds")
    parser.add_argument("end", type=float, help="End time in seconds")
    parser.add_argument("--out", default="embedding", help="Output file prefix")

    args = parser.parse_args()

    temp_wav = extract_segment(args.audio_path, args.start, args.end)
    try:
        embedding = generate_embedding(temp_wav)
        save_embedding(embedding, args.out)
    finally:
        os.remove(temp_wav)


# --- Speaker Segments ---
# SPEAKER_02: 0.0s - 1.0s (1.0s)
# SPEAKER_00: 1.0s - 2.0s (1.0s)
# SPEAKER_02: 2.0s - 4.7s (2.7s)
# SPEAKER_00: 4.7s - 20.0s (15.3s)
# SPEAKER_02: 20.3s - 28.0s (7.7s)
# SPEAKER_01: 28.0s - 30.2s (2.1s)
# SPEAKER_01: 30.6s - 49.8s (19.1s)
# SPEAKER_01: 55.0s - 64.7s (9.7s)
# SPEAKER_02: 63.5s - 63.7s (0.2s)