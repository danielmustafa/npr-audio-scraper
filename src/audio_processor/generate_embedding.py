from resemblyzer import VoiceEncoder, preprocess_wav
from pydub import AudioSegment
import numpy as np
import argparse
import tempfile
import os

def extract_segment(audio_path: str, start_sec: float, end_sec: float) -> str:
    """Extracts a segment and returns a temporary .wav file path."""
    audio = AudioSegment.from_file(audio_path)
    if start_sec and end_sec:
        segment = audio[start_sec * 1000:end_sec * 1000]  # milliseconds
        tmp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        segment.export(tmp_wav.name, format="wav")
        return tmp_wav.name
    return audio_path

def generate_embedding(segment_wav_path: str):
    print('Starting embedding generation...')
    wav = preprocess_wav(segment_wav_path)
    encoder = VoiceEncoder()
    embedding = encoder.embed_utterance(wav)
    return embedding.tolist()

def save_embedding(embedding: np.ndarray, output_path: str):
    np.save(output_path, embedding)
    print(f"Embedding saved to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio_path", help="Input audio file (.wav, .mp3, etc.)")
    parser.add_argument("--start", nargs="?", type=float, help="Start time in seconds")
    parser.add_argument("--end", nargs="?", type=float, help="End time in seconds")
    parser.add_argument("--out", default="embedding", help="Output file prefix")

    args = parser.parse_args()
    remove_file = True if args.start and args.end else False
    wav_file_path = extract_segment(args.audio_path, args.start, args.end)

    try:
        print(f"Extracted segment saved to: {wav_file_path}")
        embedding = generate_embedding(wav_file_path)
        save_embedding(embedding, args.out)
    finally:
        if remove_file:
            # Clean up the temporary file
            print(f"Removing temporary file: {wav_file_path}")
            os.remove(wav_file_path)




# 1. Scrape the audio segments from the NPR website.
# 2. For each audio URL, download the audio file.
# 3. Use the 'diarize_audio' function to segment the audio into speaker segments.
# 4. Write some logic to best guess the target speaker based on some rules
    # - Find the speaker with the most overall speaking time
    # - For audio where it's produced by one person, make an assumption that the target speaker usually starts the segment and/or ends it
# 5. Create an embedding for one segment of audio using the 'generate_embedding' function.
# 6. Save the embedding
# 7. Persist all segments with the correspondent metadata to the db
# 8. 