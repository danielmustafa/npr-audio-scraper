
import os

from util import storage_service

DEFAULT_AUDIO_TYPE = "mp3"
GCS_BUCKET_NAME = os.getenv("GCS_AUDIO_BUCKET_NAME", "npr_audio_quiz")

def get_segment(correspondent_id: int, audio_id: int, segment_id: int):
    audio_path = f"/{correspondent_id}/{audio_id}/{segment_id}.{DEFAULT_AUDIO_TYPE}"
    return storage_service.get(GCS_BUCKET_NAME, audio_path)

def save_segment(audio_metadata, segment):
    correspondent_id = audio_metadata[0]
    audio_id = audio_metadata[1]
    bucket__base_path = f"{correspondent_id}/{audio_id}"
    segment_obj = segment[0]
    segment_id = segment[1]
    storage_url, public_url = storage_service.save(segment_obj["mp3_audio_path"], GCS_BUCKET_NAME, f"{bucket__base_path}/{segment_id}.{DEFAULT_AUDIO_TYPE}")
    return storage_url, public_url
       
def save_segments(audio_metadata, segments):
    for seg in segments:
        save_segment(audio_metadata, seg)
