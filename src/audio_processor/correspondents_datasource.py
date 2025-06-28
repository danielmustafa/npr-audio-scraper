import psycopg2
from psycopg2 import pool
import numpy as np
import argparse
import os
import re


if "CORRESPONDENTS_DB_CONN_URL" not in os.environ:
    raise EnvironmentError("Environment variable CORRESPONDENTS_DB_CONN_URL must be set.")
# Initialize connection poo
db_pool = pool.SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    dsn=f"{os.environ.get("CORRESPONDENTS_DB_CONN_URL")}", 
)


def regex_type(pattern):
    def validate(value):
        if not re.match(pattern, value):
            raise argparse.ArgumentTypeError(f"Value '{value}' does not match pattern '{pattern}'")
        return value
    return validate

def split_name(fullname):
    parts = fullname.strip().split()
    if len(parts) == 0:
        return '', ''
    elif len(parts) == 1:
        return parts[0], ''
    else:
        return parts[0], ' '.join(parts[1:])
    
def correspondent_exists(cursor, fullname) -> bool:
    """Check if a correspondent with the given fullname already exists in the database."""
    if not fullname:
        raise ValueError("Fullname cannot be empty.")
    cursor.execute("""
        SELECT id FROM correspondents WHERE fullname = %s
    """, (fullname,))
    return cursor.fetchone() is not None

def get_correspondent_by_name(fullname: str):
    # conn = db_pool.getconn()
    conn = db_pool.getconn()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            select id, fullname, gender from correspondents where fullname = %s
                       """, (fullname,))
        
        results = cursor.fetchone()
        return results
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        cursor.close()
        db_pool.putconn(conn)

# Check if an embedding exists based on comparison
# or.. Get embeddings within a certain distance
def get_embeddings_by_similarity(min_threshold: float, embedding):
    # Connect to DB
    conn = db_pool.getconn()
    cursor = conn.cursor()

    try:
        # Insert into correspondents
        cursor.execute("""
            select id, fullname, gender, similarity from 
            (select id, fullname, gender, 1 - (embedding <=> %s::vector) AS similarity from correspondents)
            where similarity > %s
            ORDER BY similarity DESC
        """, (embedding, min_threshold))
        
        results = cursor.fetchall()
        if not results:
            print("No correspondents found with embeddings above the threshold.")
            return []
        return results
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        cursor.close()
        db_pool.putconn(conn)

def create_correspondent(fullname, gender, embedding_path):
    # Load embedding from file
    if not os.path.exists(embedding_path):
        raise FileNotFoundError(f"Embedding file '{embedding_path}' not found.")
    embedding = np.load(embedding_path).tolist()  # Converts to list for persistence

    # Connect to DB
    conn = db_pool.getconn()
    cursor = conn.cursor()

    try:
        # Insert into correspondents
        cursor.execute("""
            INSERT INTO correspondents (fullname, gender, embedding)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (fullname, gender.upper(), embedding))
        correspondent_id = cursor.fetchone()[0]

        conn.commit()
        print(f"✅ Inserted correspondent '{fullname}' with ID {correspondent_id} and embedding.")

    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")

    finally:
        cursor.close()
        db_pool.putconn(conn)

def create_correspondent_from_embedding(fullname, gender, embedding):
    """Insert a correspondent using a provided embedding list[float]."""
    # Connect to DB
    conn = db_pool.getconn()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO correspondents (fullname, gender, embedding)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (fullname, gender.upper(), embedding)
        )
        correspondent_id = cursor.fetchone()[0]
        conn.commit()
        print(f"✅ Inserted correspondent '{fullname}' with ID {correspondent_id} and embedding.")
        return correspondent_id
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        cursor.close()
        db_pool.putconn(conn)

def create_audio(correspondent_id: int, url: str) -> int:
    """Insert a new audio record and return its id."""
    conn = db_pool.getconn()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO audio (correspondent_id, url)
            VALUES (%s, %s)
            RETURNING id
            """,
            (correspondent_id, url)
        )
        audio_id = cursor.fetchone()[0]
        conn.commit()
        print(f"✅ Inserted audio record for correspondent_id {correspondent_id} with id {audio_id}.")
        return audio_id
    except Exception as e:
        conn.rollback()
        print(f"❌ Error inserting audio record: {e}")
        raise
    finally:
        cursor.close()
        db_pool.putconn(conn)

def create_audio_segments(segments: list[dict]) -> list[int]:
    """Bulk insert multiple audio segments and return their ids."""
    conn = db_pool.getconn()
    cursor = conn.cursor()
    ids = []
    try:
        # Prepare data for bulk insert
        values = [
            (seg['audio_id'], seg['start_time_sec'], seg['end_time_sec'], seg['end_time_sec'] - seg['start_time_sec'])
            for seg in segments
        ]
        # Use execute_values for efficient bulk insert
        from psycopg2.extras import execute_values
        query = """
            INSERT INTO audio_segments (audio_id, start_time_sec, end_time_sec, duration_sec)
            VALUES %s
            RETURNING id
        """
        execute_values(cursor, query, values)
        ids = [row[0] for row in cursor.fetchall()]
        conn.commit()
        print(f"✅ Bulk inserted {len(ids)} audio segment(s). IDs: {ids}")
        return ids
    except Exception as e:
        conn.rollback()
        print(f"❌ Error inserting audio segments: {e}")
        raise
    finally:
        cursor.close()
        db_pool.putconn(conn)

def update_audio_segment_storage_url(audio_id: int, segment_id: int, url: str) -> bool:
    """
    Update the url for a specific audio segment in the audio_segments table.
    Returns True if a row was updated, False otherwise.
    """
    conn = db_pool.getconn()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE audio_segments
            SET storage_url = %s
            WHERE audio_id = %s AND id = %s
            """,
            (url, audio_id, segment_id)
        )
        updated = cursor.rowcount > 0
        conn.commit()
        # print(f"Updated url for audio_id={audio_id}, segment_id={segment_id}: {updated}")
        return updated
    except Exception as e:
        conn.rollback()
        print(f"❌ Error updating audio segment storage url: {e}")
        return False
    finally:
        cursor.close()
        db_pool.putconn(conn)

def update_audio_segment_public_url(segment_id: int, public_url: str) -> bool:
    """
    Update the public url for a specific audio segment in the audio_segments table.
    Returns True if a row was updated, False otherwise.
    """
    conn = db_pool.getconn()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE audio_segments
            SET public_url = %s
            WHERE id = %s
            """,
            (public_url, segment_id)
        )
        updated = cursor.rowcount > 0
        conn.commit()
        # print(f"Updated url for audio_id={audio_id}, segment_id={segment_id}: {updated}")
        return updated
    except Exception as e:
        conn.rollback()
        print(f"❌ Error updating audio segment public_url: {e}")
        return False
    finally:
        cursor.close()
        db_pool.putconn(conn)

def get_quiz_metadata():
    """
    Returns a randomized quiz object model containing a list of quiz questions with 
    a correct correspondent, audio url, and multiple choice options.
    """
    conn = db_pool.getconn()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            with random_correspondents AS (
            SELECT id AS correspondent_id
            FROM correspondents
            ORDER BY random()
            LIMIT 10
            ),
            random_segments AS (
            SELECT DISTINCT ON (corr.id)
                corr.id AS correct_correspondent_id,
                corr.fullname AS correct_correspondent_name,
                corr.gender AS correct_correspondent_gender,
                asegs.public_url AS audio_url
            FROM 
                random_correspondents rc
                JOIN correspondents corr ON corr.id = rc.correspondent_id
                JOIN audio ON audio.correspondent_id = corr.id
                JOIN audio_segments asegs ON audio.id = asegs.audio_id
            ORDER BY corr.id, random()
            ),
            question_with_options AS (
            SELECT 
                rs.*,
                (
                SELECT json_agg(json_build_object('id', id, 'fullname', fullname))
                FROM (
                    SELECT id, fullname FROM (
                    -- Select 3 random incorrect correspondents
                    SELECT c.id, c.fullname
                    FROM correspondents c
                    WHERE c.id != rs.correct_correspondent_id
                    AND c.gender = rs.correct_correspondent_gender
                    ORDER BY random()
                    LIMIT 3
                    ) distractors

                    UNION ALL

                    -- Include the correct correspondent
                    SELECT rs.correct_correspondent_id, rs.correct_correspondent_name
                ) all_choices
                ORDER BY random()
                ) AS multiple_choice
            FROM random_segments rs
            )
            SELECT json_agg(row_to_json(payload)) FROM 
            (select
                correct_correspondent_id correspondent_id,
                correct_correspondent_name correspondent_name,
                audio_url,
                multiple_choice options
                from question_with_options
            ) payload
            """
        )
        result = cursor.fetchone()
        # print(f"Updated url for audio_id={audio_id}, segment_id={segment_id}: {updated}")
        return result
    except Exception as e:
        conn.rollback()
        print(f"❌ Error generating quiz metadata: {e}")
        return False
    finally:
        cursor.close()
        db_pool.putconn(conn)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--fullname", type=regex_type(r"\w+"), required=True, help="Full name of the correspondent")
    parser.add_argument("--gender", type=regex_type(r"^[mMfFuU]$"), required=True, help="Gender of the correspondent (m = male, f = female, u = unspecified)")
    parser.add_argument("--embedding", required=True, help="Path to the .npy embedding file")

    args = parser.parse_args()

    db_url = os.environ.get("CORRESPONDENTS_DB_CONN_URL")
    if not db_url:
        raise EnvironmentError("Environment variable CORRESPONDENTS_DB_CONN_URL must be set.")

    create_correspondent(args.fullname, args.gender, args.embedding)

#postgresql://user:password@host:port/database
