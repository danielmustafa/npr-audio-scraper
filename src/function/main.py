from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
import os

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["GET", "POST", "OPTIONS"], allow_headers=["*"])

SECRETS_PATH = os.getenv("SECRETS_PATH", "/etc/secrets")
with open(f"{SECRETS_PATH}/xata-api-token", 'r') as f:
    XATA_API_KEY = f.read().strip()

XATA_API_URL = os.getenv("XATA_API_URL", "https://danielmustafa-s-workspace-b2b2e6.us-east-1.xata.sh/db/npr-audio-quiz:main/sql")

DEFAULT_GENERATE_QUIZ_SQL = """
with random_correspondents as( select id as correspondent_id from correspondents order by random() limit 10), random_segments as( select distinct on (corr.id) corr.id as correct_correspondent_id, corr.fullname as correct_correspondent_name, corr.gender as correct_correspondent_gender, asegs.public_url as audio_url from random_correspondents rc join correspondents corr on corr.id = rc.correspondent_id join audio on audio.correspondent_id = corr.id join audio_segments asegs on audio.id = asegs.audio_id order by corr.id, random()), question_with_options as ( select rs.correct_correspondent_id correspondent_id, rs.correct_correspondent_name correspondent_name, rs.audio_url, ( select json_agg(json_build_object('id', id, 'full_name', fullname, 'is_answer', isanswer)) from ( select id, fullname, isanswer from ( select c.id, c.fullname, 'false'::boolean isanswer from correspondents c where c.id != rs.correct_correspondent_id and c.gender = rs.correct_correspondent_gender order by random() limit 3 ) distractors union all select rs.correct_correspondent_id, rs.correct_correspondent_name, 'true'::boolean isanswer ) all_choices order by random() ) as options from random_segments rs ) select audio_url, encode(cast(options::text as bytea), 'hex') options from question_with_options
"""

GENERATE_QUIZ_SQL = os.getenv("GENERATE_QUIZ_SQL", DEFAULT_GENERATE_QUIZ_SQL)


def post(request):
    try:
        res = requests.post(
            XATA_API_URL,
            headers={"Authorization": f"Bearer {XATA_API_KEY}"},
            json=request
        )
    except requests.RequestException as e:
        print(f"Error connecting to Xata API: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving quiz details")

    if res.status_code != 200:
        raise HTTPException(status_code=res.status_code, detail="Failed to retrieve quiz data")
    
    return res.json()

@app.get("/generate-quiz")
def generate_quiz():

    quiz_data = post({"statement": GENERATE_QUIZ_SQL})

    result = {
        "quiz": quiz_data.get("records", []),
        "metadata": {
            "total_questions": len(quiz_data.get("records", [])),
        }
    }
    return JSONResponse(content=result)

@app.get("/health")
def health_check():
    res = post({"statement": "SELECT 1"})
    return JSONResponse(content={"status": "ok"})