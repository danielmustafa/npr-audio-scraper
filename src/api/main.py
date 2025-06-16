from fastapi import FastAPI, Response
from audio_processor import correspondents_datasource
from io import BytesIO
app = FastAPI()

@app.get("/hello")
def hello_world():
    return {"message": "Hello, world!"}

@app.get("/api/audio-quiz")
def get_audio_quiz():
    quiz_metadata = correspondents_datasource.get_quiz_metadata()
    return quiz_metadata