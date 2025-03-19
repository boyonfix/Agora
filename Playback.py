from pydub import AudioSegment
import sqlite3
from datetime import datetime
import time
import os

BASE_DIR = r"mypath"
DB_PATH = os.path.join(BASE_DIR, "MemoriaFM.db")
CATEGORY_AUDIO_PATH = os.path.join(BASE_DIR, "CategoryAudio")
AUDIO_FOLDER_PATH = os.path.join(BASE_DIR, "AudioRecordings")

def playback_audio_with_full_navigation_and_recording(category_id, mode, db_path):
    """
    Play audio dynamically with track navigation, in-track seek, and recording/remix functionality.

    Parameters:
        category_id (int): The ID of the selected category (either topic ID or year).
        mode (str): Playback mode, either 'topic' or 'time'.
        db_path (str): Path to the SQLite database.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    if mode == "topic":
        cursor.execute("SELECT id, file_path FROM recordings WHERE category_id = ?", (category_id,))
    elif mode == "time":
        cursor.execute("""
            SELECT id, file_path
            FROM recordings
            WHERE strftime('%Y', creation_date) = ?
        """, (str(category_id),))
    else:
        print("Invalid mode. Please select 'topic' or 'time'.")
        conn.close()
        return

    audio_files = cursor.fetchall()
    conn.close()

    if not audio_files:
        print("No audio files found for the selected category.")
        return

    print(f"Playing {len(audio_files)} audio files in category ID {category_id}.")

    current_track_index = 0
    current_position = 0  
    is_playing = True
    is_recording = False
    recording_mode = None  

    while is_playing:
        track_id, current_audio_file = audio_files[current_track_index]
        current_audio = AudioSegment.from_file(current_audio_file)
        audio_duration = len(current_audio) / 1000  

        print(f"Now playing: {current_audio_file} (Track {current_track_index + 1} of {len(audio_files)})")

        while current_position < audio_duration:
            print(f"Current playback position: {current_position:.2f} seconds")
            current_position += 1  
            time.sleep(1)

            forward_button_pressed = False
            backward_button_pressed = False
            rewind = False
            fast_forward = False
            remix_button_pressed = False
            standard_recording_button_pressed = False
            recording_start_button_pressed = False
            recording_cancel_button_pressed = False

            if forward_button_pressed:
                if current_track_index < len(audio_files) - 1:
                    current_track_index += 1
                    current_position = 0  
                    print("Skipping to the next track...")
                    break
                else:
                    print("End of playlist reached.")
                    is_playing = False
                    break

            if backward_button_pressed:
                if current_track_index > 0:
                    current_track_index -= 1
                    current_position = 0  
                    print("Returning to the previous track...")
                    break
                else:
                    print("Already at the first track.")
                    current_position = 0  
                    continue

            if rewind:
                current_position = max(0, current_position - 5)  
                print(f"Rewinding to: {current_position:.2f} seconds")
                continue

            if fast_forward:
                current_position = min(audio_duration, current_position + 5)  
                print(f"Fast-forwarding to: {current_position:.2f} seconds")
                continue

            if remix_button_pressed:
                recording_mode = "remix"
                print("Remix mode activated. Press the recording start button to begin.")
                continue

            if standard_recording_button_pressed:
                recording_mode = "standard"
                print("Standard recording mode activated. Press the recording start button to begin.")
                continue

            if recording_start_button_pressed and recording_mode:
                print(f"Starting {recording_mode} recording. Pausing playback...")
                is_recording = True
                current_position_at_pause = current_position

                if recording_mode == "remix":
                    remix_file = "/path/to/recorded_remix_file.mp3"  
                    mix_audio_with_remix_and_save(
                        original_file=current_audio_file,
                        remix_file=remix_file,
                        pause_time=current_position,
                        db_path=db_path,
                        original_id=track_id,
                        category_id=category_id
                    )
                elif recording_mode == "standard":
                    simulate_standard_recording()  
                print(f"{recording_mode.capitalize()} recording complete. Resuming playback...")
                is_recording = False
                recording_mode = None
                current_position = current_position_at_pause
                continue

            if recording_cancel_button_pressed and is_recording:
                print("Recording canceled. Resuming playback...")
                is_recording = False
                recording_mode = None
                current_position = current_position_at_pause
                continue

            if current_position >= audio_duration:
                if current_track_index < len(audio_files) - 1:
                    current_track_index += 1
                    current_position = 0
                else:
                    print("All tracks in the category have been played.")
                    is_playing = False

    print("Playback complete.")

def simulate_standard_recording():
    """
    Simulate the standard recording process.
    """
    print("Recording standard audio...")
    time.sleep(3)  
    print("Standard recording complete.")

    Placeholder for mixing audio with remix functionality.
    """
    print(f"Mixing audio: {original_file} + {remix_file} at {pause_time} seconds.")
    print(f"Saving remix to database under category {category_id} with reference to original ID {original_id}.")
