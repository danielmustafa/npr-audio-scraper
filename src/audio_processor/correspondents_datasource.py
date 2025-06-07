import psycopg2
import numpy as np
import argparse
import os
import re

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

def get_correspondent_by_name(db_url: str, fullname: str):
    conn = psycopg2.connect(db_url)
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
        conn.close()

# Check if an embedding exists based on comparison
# or.. Get embeddings within a certain distance
def get_embeddings_by_similarity(db_url: str, min_threshold: float, embedding):
    # Connect to DB
    conn = psycopg2.connect(db_url)
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
        conn.close()

def create_correspondent(db_url, fullname, gender, embedding_path):
    # Load embedding from file
    if not os.path.exists(embedding_path):
        raise FileNotFoundError(f"Embedding file '{embedding_path}' not found.")
    embedding = np.load(embedding_path).tolist()  # Converts to list for persistence

    # Connect to DB
    conn = psycopg2.connect(db_url)
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
        conn.close()

def create_correspondent_from_embedding(db_url, fullname, gender, embedding):
    """Insert a correspondent using a provided embedding list[float]."""
    # Connect to DB
    conn = psycopg2.connect(db_url)
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
        conn.close()

def create_audio(db_url: str, correspondent_id: int, url: str) -> int:
    """Insert a new audio record and return its id."""
    conn = psycopg2.connect(db_url)
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
        conn.close()

def create_audio_segments(db_url: str, segments: list[dict]) -> list[int]:
    """Bulk insert multiple audio segments and return their ids."""
    conn = psycopg2.connect(db_url)
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
        conn.close()



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--fullname", type=regex_type(r"\w+"), required=True, help="Full name of the correspondent")
    parser.add_argument("--gender", type=regex_type(r"^[mMfFuU]$"), required=True, help="Gender of the correspondent (m = male, f = female, u = unspecified)")
    parser.add_argument("--embedding", required=True, help="Path to the .npy embedding file")

    args = parser.parse_args()

    db_url = os.environ.get("CORRESPONDENTS_DB_CONN_URL")
    if not db_url:
        raise EnvironmentError("Environment variable CORRESPONDENTS_DB_CONN_URL must be set.")

    create_correspondent(db_url, args.fullname, args.gender, args.embedding)

#postgresql://user:password@host:port/database
