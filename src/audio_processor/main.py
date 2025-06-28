import audio_scraper
import diarize_audio
import argparse
import generate_embedding
import correspondents_datasource
import os
import audio_storage
from diarize_audio import download_audio
from audio_editor import extract_segment, convert_type

BASE_API_PATH = "/api/audio"
MIN_SIMILARITY_THRESHOLD = 0.80
GCS_BUCKET_NAME = "npr_audio_quiz"
DEFAULT_AUDIO_TYPE = "mp3"
# 
WORKING_DIR = "downloads"
def process_story(story, db_url):
    print("\n======================")
    print(f"Processing story for correspondent: {story['correspondent_name']}, \nAudio URL: {story['audio_url']}")
    try:
        audio_url = story['audio_url']
        # Determine expected wav path
        # TODO clean this shit up
        # parsed = os.path.splitext(os.path.basename(audio_url))
        # audio_filename = parsed[0] + ".mp3"
        audio_filename = os.path.basename(audio_url)
        mp3_audio_path = os.path.join(WORKING_DIR, audio_filename) #downloads/filename.mp3
        if not os.path.exists(mp3_audio_path):
            mp3_audio_path = download_audio(audio_url)
        
        wav_audio_path = convert_type(mp3_audio_path, "wav")

        # diarize audio
        segments = diarize_audio.diarize_audio(wav_audio_path)
        speaker_ids: set[int] = set()
        for seg in segments:
            speaker_ids.add(seg['speaker_id'])
            print(f"Id: {seg['segment_id']}, Speaker: {seg['speaker_id']}, Start: {seg['start_time']:.1f}s, End: {seg['end_time']:.1f}s, Duration: {seg['duration_sec']:.1f}s")

        speaker_id = input(f"\nEnter the speaker ID to filter segments, or press Enter to skip {list(speaker_ids)}: ").strip()

        if speaker_id not in speaker_ids:
            return

        filtered_segments = get_filtered_segments(segments, speaker_id)

        segment_ids = sorted(set(map(lambda x: int(x['segment_id']), filtered_segments)))

        segment_to_embed_id = input(f"Enter the segment ID to use for embedding {segment_ids}: ").strip()

        segment_id_input = input(f"Enter the segment ids to be used for audio segments, or press Enter to use all of them {segment_ids}: ").strip()
        if segment_id_input:
            selected_segment_ids = set(segment_id_input.split(','))
            selected_segments = [seg for seg in filtered_segments if str(seg['segment_id']) in selected_segment_ids]
        else:
            selected_segments = filtered_segments

        if not selected_segments:
            print("No segments selected for audio segments.")
            return
        
        segment_for_embedding = next((seg for seg in selected_segments if str(seg['segment_id']) == segment_to_embed_id), None)
        embedding = create_embedding(wav_audio_path, segment_for_embedding)

        story['correspondent_gender'] = input(f"Enter gender of correspondent {story['correspondent_name']} (M/F/U): ").strip().upper()
        
        if not story['correspondent_gender']:
            story['correspondent_gender'] = 'U'  # Default to unknown if not provided

        # create audio segments in mp3
        for seg in selected_segments:
            # seg_filename = f'{story["correspondent_name"]}_{seg["segment_id"]}'
            seg["mp3_audio_path"] = extract_segment(mp3_audio_path,  seg['start_time'], seg['end_time'], "mp3")
            # print(seg["mp3_audio_path"])

        #(correspondent_id, audio_id, segment_ids)
        audio_metadata = handle_db_operations(db_url, story, embedding, selected_segments)
        segments_with_id = zip(selected_segments, audio_metadata[2]) #(segment, segment_id) this is kinda sloppy

        for seg in segments_with_id:
            storage_url, public_url = audio_storage.save_segment(audio_metadata, seg)
            correspondents_datasource.update_audio_segment_storage_url(audio_metadata[1], seg[1], storage_url) 
            correspondents_datasource.update_audio_segment_public_url(seg[1], public_url)
        
    finally:
        # Clean up the downloaded audio file if it was downloaded in this run
        cleanup_audio(wav_audio_path)
        cleanup_audio(mp3_audio_path)
        for seg in selected_segments:
            cleanup_audio(seg["mp3_audio_path"])

        print(f"Completed for correspondent: {story['correspondent_name']}")
        print("\n======================")
        

# def save_segments(db_url, audio_metadata, segments):
#     audio_id = audio_metadata[1]
#     bucket__base_path = f"{audio_metadata[0]}/{audio_id}"
#     for seg in segments:
#         segment_id = seg[1]
#         storage_url = storage_service.save(seg[0]["mp3_audio_path"], GCS_BUCKET_NAME, f"{bucket__base_path}/{segment_id}.{DEFAULT_AUDIO_TYPE}")
#         correspondents_datasource.update_audio_segment_storage_url(db_url, audio_id, segment_id, storage_url)

def cleanup_audio(audio_path):
    if audio_path and os.path.exists(audio_path):
        try:
            os.remove(audio_path)
            print(f"Deleted audio file: {audio_path}")
        except Exception as e:
            print(f"Failed to delete audio file {audio_path}: {e}")


def create_embedding(wav_audio_path, segment_for_embedding):    
    if not segment_for_embedding:
        print("No segment found for embedding with the given segment_id.")
        return
    
    segment_wav_path = extract_segment(wav_audio_path, segment_for_embedding['start_time'], segment_for_embedding['end_time'], "wav")
    embedding = generate_embedding.generate_embedding(segment_wav_path)
    return embedding


def get_filtered_segments(segments, speaker_id):
    return [seg for seg in segments if seg['speaker_id'] == speaker_id and seg['duration_sec'] > 10.0]

def print_long_segments(long_segments):
    print("Segments for this speaker over 10 seconds:")
    for seg in long_segments:
        print(f"Start: {seg['start_time']:.1f}s, End: {seg['end_time']:.1f}s, Duration: {seg['duration_sec']:.1f}s")

def handle_db_operations(db_url, story, embedding, segments):
    # results = correspondents_datasource.get_embeddings_by_similarity(db_url, MIN_SIMILARITY_THRESHOLD, embedding)
    correspondent_name = story['correspondent_name']
    correspondent_audio_url = story['audio_url']
    correspondent_gender = story['correspondent_gender']
    result = correspondents_datasource.get_correspondent_by_name(correspondent_name)
    if result:
        print("Found embedding(s) with high similarity score.  Skipping creation of new correspondent...")
        for row in result:
            print(row)
        correspondent_id = result[0]  # Assuming tuple (id, ...)
        try:
            audio_id = correspondents_datasource.create_audio(correspondent_id, correspondent_audio_url)
            print(f"Created new audio record with id: {audio_id}")
            audio_segments = [
                {
                    'audio_id': audio_id,
                    'start_time_sec': seg['start_time'],
                    'end_time_sec': seg['end_time']
                }
                for seg in segments
            ]
            segment_ids = correspondents_datasource.create_audio_segments(audio_segments)
            print(f"Inserted audio segments with ids: {segment_ids}")
        except Exception as e:
            if 'duplicate key value violates unique constraint' in str(e):
                print("Audio record already exists. Skipping audio and segment insertion.")
            else:
                print(f"Error inserting audio: {e}")
                raise
    else:
        print("No similarity results found. Creating new correspondent...")
        correspondent_id = correspondents_datasource.create_correspondent_from_embedding(correspondent_name, correspondent_gender, embedding)
        print(f"🗣️ Created new correspondent with id: {correspondent_id}")
        audio_id = correspondents_datasource.create_audio(correspondent_id, correspondent_audio_url)
        print(f"🎵 Created new audio record with id: {audio_id}")
        audio_segments = [
            {
                'audio_id': audio_id,
                'start_time_sec': seg['start_time'],
                'end_time_sec': seg['end_time']
            }
            for seg in segments
        ]
        segment_ids = correspondents_datasource.create_audio_segments(audio_segments)
        print(f"Inserted audio segments with ids: {segment_ids}")
    return (correspondent_id, audio_id, segment_ids)

# Create a map of month names with the key of number and value of month name
month_map = {
    '01': 'january',
    '02': 'february',
    '03': 'march',
    '04': 'april',
    '05': 'may',
    '06': 'june',
    '07': 'july',
    '08': 'august',
    '09': 'september',
    '10': 'october',
    '11': 'november',
    '12': 'december'
}


def main():

    if not os.environ.get("CORRESPONDENTS_DB_CONN_URL"):
        print("CORRESPONDENTS_DB_CONN_URL environment variable not set.")
        return

    parser = argparse.ArgumentParser()
    parser.add_argument("--add", action='store_true', help="If supplied, must supply --url and -correspondent")
    parser.add_argument("--audio_url", nargs="?", type=str, help="Start time in seconds")
    parser.add_argument("--correspondent", nargs="?", type=str, help="End time in seconds")
    parser.add_argument("--date", nargs="?", type=str, help="Date in YYYY-MM-DD format")
    db_url = os.environ.get("CORRESPONDENTS_DB_CONN_URL")
    args = parser.parse_args()
    print(args)
    if args.add and args.audio_url and args.correspondent:
        process_story({
            'audio_url': args.audio_url,
            'correspondent_name': args.correspondent
        }, db_url)    

    elif args.date:
        date_path = args.date.replace('-', '/')
        date_with_month = f'{month_map[args.date[5:7]]}-{args.date[8:10]}-{args.date[:4]}'
        me_site = f'https://www.npr.org/programs/morning-edition/{date_path}/morning-edition-for-{date_with_month}'
        atc_site = f'https://www.npr.org/programs/all-things-considered/{date_path}/all-things-considered-for-{date_with_month}'
        
        me_stores = audio_scraper.scrape_stories(me_site)
        atc_stories = audio_scraper.scrape_stories(atc_site)
        stories = me_stores + atc_stories
        for story in stories:
            process_story(story, db_url)





if __name__ == "__main__":
    main()