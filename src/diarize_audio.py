import os
import requests
import torch
from pyannote.audio import Pipeline
from pydub import AudioSegment
from urllib.parse import urlparse

<<<<<<< HEAD
=======
HUGGINGFACE_TOKEN = None
>>>>>>> cff05ca (adding diarize)

def download_audio(url: str, output_folder: str = "downloads") -> str:
    # os.makedirs(output_folder, exist_ok=True)
    # parsed = urlparse(url)
    # filename = os.path.basename(parsed.path) or "audio.mp3"
    # filepath = os.path.join(output_folder, filename)

    # print(f"Downloading {url}...")
    # response = requests.get(url, stream=True)
    # response.raise_for_status()
    # with open(filepath, "wb") as f:
    #     for chunk in response.iter_content(chunk_size=8192):
    #         f.write(chunk)
    # print(f"Saved to {filepath}")

    filepath = url
    return filepath

def convert_to_wav(mp3_path: str) -> str:
    audio = AudioSegment.from_file(mp3_path)
    wav_path = mp3_path.rsplit(".", 1)[0] + ".wav"
    audio.export(wav_path, format="wav")
    return wav_path

def diarize_audio(wav_path: str):
    pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", use_auth_token=os.getenv("HUGGINGFACE_TOKEN"))
    # pipeline.to(torch.device("cuda"))
    diarization = pipeline(wav_path)

    print("\n--- Speaker Segments ---")
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        duration = turn.end - turn.start
        print(f"{speaker}: {turn.start:.1f}s - {turn.end:.1f}s ({duration:.1f}s)")

if __name__ == "__main__":
    audio_url = input("Enter audio URL: ").strip()
    downloaded_path = download_audio(audio_url)
    wav_path = convert_to_wav(downloaded_path)
    diarize_audio(wav_path)
