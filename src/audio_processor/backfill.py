import os
import psycopg2
from diarize_audio import download_audio
from audio_editor import extract_segment
from correspondents_datasource import update_audio_segment_storage_url, db_pool
from main import save_segments, cleanup_audio

def get_missing_url_records():
    # Connect to DB
    db_url = os.getenv("CORRESPONDENTS_DB_CONN_URL")
    conn = db_pool.getconn()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            select 
                a.id,
                a.correspondent_id,
                a.url,
                aseg.id seg_id,
                aseg.start_time_sec::float,
                aseg.end_time_sec::float
                from audio a
                join audio_segments aseg
                on a.id = aseg.audio_id
                and aseg.start_time_sec::float = 0.0
        """)
        
        results = cursor.fetchall()
        if not results:
            print("No records found.")
            return []
        return results
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        cursor.close()
        db_pool.putconn(conn)

def main():
    db_url = os.getenv("CORRESPONDENTS_DB_CONN_URL")
    records = get_missing_url_records()

    for record in records:
        print(f"starting: {record}")
        audio_id = record[0]
        correspondent_id = record[1]
        audio_url = record[2]
        segment_id = record[3]
        start_time_sec = record[4]
        end_time_sec = record[5]
        audio_filename = os.path.basename(audio_url)
        mp3_audio_path = os.path.join("downloads", audio_filename) #downloads/filename.mp3

        try:
            if not os.path.exists(mp3_audio_path):
                mp3_audio_path = download_audio(audio_url)

            segment_path = extract_segment(mp3_audio_path,  start_time_sec, end_time_sec, "mp3")
            save_segments(db_url, (correspondent_id, audio_id), [({"mp3_audio_path": segment_path}, segment_id)])
        finally:
            pass
            # cleanup_audio(segment_path)


if __name__ == "__main__":
    main()