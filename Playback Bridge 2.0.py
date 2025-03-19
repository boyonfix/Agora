import os
import serial
import sqlite3
import time
from threading import Thread
from queue import Queue
import psutil
import wave
import pyaudio
from mutagen import File
from mutagen.mp4 import MP4
import subprocess

# Paths to database and audio files
DB_PATH = r"C:\Users\relle\OneDrive\Desktop\Agora\Database\MemoriaFM.db"
RAW_WAV_FOLDER = r"C:\Users\relle\OneDrive\Desktop\Agora\Raw_Wav"

# Shared state
rotation_counts = Queue()
recording_active = False
recording_stream = None
recording_frames = []  # To store audio frames during recording
audio = pyaudio.PyAudio()

def stop_current_audio():
    """Stop the current audio playback by killing the audio player process."""
    for process in psutil.process_iter(attrs=["pid", "name"]):
        if process.info["name"] in ["Microsoft.Media.Player.exe"]:  # Adjust for the default audio player
            print(f"Stopping audio player process with PID: {process.info['pid']}")
            process.terminate()
            try:
                process.wait(timeout=1)
                print("Audio playback stopped.")
            except psutil.TimeoutExpired:
                print("Failed to stop playback within timeout.")
            return
    print("No audio player process found to stop.")

def get_audio_duration(file_path):
    """Retrieve the duration of an audio file in seconds using ffprobe."""
    try:
        command = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "a:0",
            "-show_entries", "stream=duration",
            "-of", "csv=p=0",
            file_path
        ]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            duration = float(result.stdout.strip())
            print(f"Duration of {file_path}: {duration} seconds")
            return duration
        else:
            print(f"ffprobe error for file {file_path}: {result.stderr.strip()}")
            return None
    except Exception as e:
        print(f"Error retrieving duration for {file_path}: {e}")
        return None

def play_category_name_audio(category_id, db_path):
    """
    Fetch the name audio path for the given category ID and play it if it exists.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Fetch the name audio path for the category
    cursor.execute("SELECT name_audio_path FROM categories WHERE id = ?", (category_id,))
    result = cursor.fetchone()
    conn.close()

    if not result or not result[0]:
        print(f"Category ID {category_id} has no name audio. Skipping.")
        return

    name_audio_path = result[0]
    if not os.path.exists(name_audio_path):
        print(f"Category name audio file does not exist: {name_audio_path}. Skipping.")
        return

    print(f"Playing category name audio: {name_audio_path}")
    try:
        os.startfile(name_audio_path)

        # Wait for the duration of the audio or detect user interruption
        duration = get_audio_duration(name_audio_path)
        if duration:
            print(f"Category name audio duration: {duration:.2f} seconds")
            time.sleep(duration)  # Wait for the duration of the audio to finish
        else:
            print("Could not determine the duration of the category name audio.")
    except Exception as e:
        print(f"Error playing category name audio: {e}")

def start_recording():
    """Start recording audio from the microphone."""
    global recording_stream, recording_frames, recording_active

    print("Starting recording...")
    recording_frames = []  # Reset the frame buffer
    recording_active = True  # Ensure the recording thread stays active
    try:
        recording_stream = audio.open(format=pyaudio.paInt16,
                                       channels=1,
                                       rate=8000,
                                       input=True,
                                       frames_per_buffer=1024)
        print("Recording stream opened successfully.")
    except Exception as e:
        print(f"Failed to open recording stream: {e}")
        recording_active = False  # Fail-safe

    def record():
        print("Recording thread started.")
        while recording_active:
            try:
                data = recording_stream.read(1024, exception_on_overflow=False)
                recording_frames.append(data)
                print(f"Captured {len(data)} bytes of audio data.")
            except Exception as e:
                print(f"Error during recording: {e}")
                break
        print("Recording thread ended.")

    Thread(target=record, daemon=True).start()

def stop_recording():
    """Stop the recording process and save the audio to a file."""
    global recording_stream, recording_frames, recording_active

    print("Stopping recording...")
    print(f"Recording active state before stopping: {recording_active}")
    recording_active = False  # Ensure the recording thread stops

    if recording_stream:
        print("Stopping recording stream...")
        recording_stream.stop_stream()
        recording_stream.close()
        recording_stream = None

        # Save the recorded data to a WAV file
        recording_file = os.path.join(RAW_WAV_FOLDER, "temp_recording.wav")
        if recording_frames:
            try:
                with wave.open(recording_file, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
                    wf.setframerate(8000)
                    wf.writeframes(b''.join(recording_frames))
                print(f"Recording saved to {recording_file}. Total frames: {len(recording_frames)}")
            except Exception as e:
                print(f"Error saving recording: {e}")
        else:
            print("No frames were captured. Recording was empty.")
    else:
        print("Recording stream was not active.")

def playback_audio_with_navigation(category_id, mode, db_path):
    """
    Play category name audio (if exists) and then audio sequentially based on the selected category and mode.
    """
    # Play the category name audio first
    play_category_name_audio(category_id, db_path)

    # Fetch recordings in the category
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
        print(f"No audio files found for category ID {category_id} in mode {mode}.")
        return

    print(f"Playing {len(audio_files)} files in {mode} mode.")
    for track_id, file_path in audio_files:
        # Check if a new rotation count interrupts the playback
        if not rotation_counts.empty():
            print("New rotation detected during playback. Stopping current category.")
            break

        if not os.path.exists(file_path):
            print(f"File not found: {file_path}. Skipping.")
            continue

        try:
            print(f"Now playing: {file_path} (Track ID: {track_id})")

            # Get the duration of the audio file
            duration = get_audio_duration(file_path)
            if duration is None:
                print(f"Skipping {file_path} due to missing duration.")
                continue

            # Start playback with the system's default audio player
            os.startfile(file_path)

            # Wait for the duration of the file or detect an interruption
            start_time = time.time()
            while time.time() - start_time < duration:
                if not rotation_counts.empty():
                    print("New rotation detected during playback. Interrupting current audio.")
                    return  # Exit playback loop to handle new category

                time.sleep(0.1)  # Check every 100ms

            # Add a small gap before the next file
            time.sleep(0.5)

        except Exception as e:
            print(f"Error playing audio file {file_path}: {e}")
            continue

    print("Finished playing all files in the current category.")

def serial_worker(serial_port, baud_rate=9600):
    """Handle serial communication with the Arduino."""
    global recording_active, recording_frames

    try:
        with serial.Serial(serial_port, baud_rate, timeout=1) as arduino:
            print("Connected to Arduino successfully.")
            while True:
                if arduino.in_waiting > 0:
                    message = arduino.readline().decode('utf-8').strip()
                    print(f"Received from Arduino: {message}")

                    if message == "Microphone Activated":
                        if not recording_active:
                            print("Starting recording...")
                            stop_current_audio()  # Interrupt playback
                            start_recording()  # Begin recording
                            recording_active = True

                    elif message == "Microphone Deactivated":
                        if recording_active:
                            print("Stopping recording...")
                            stop_recording()  # Stop recording and save file
                            recording_active = False

                    elif message.startswith("Rotation Count:"):
                        try:
                            count = int(message.split(":")[1].strip())
                            print(f"Queueing rotation count: {count}")
                            rotation_counts.put(count)  # Push the new rotation count
                        except (ValueError, IndexError):
                            print(f"Error parsing rotation count: {message}")

    except serial.SerialException as e:
        print(f"Error communicating with Arduino: {e}")

def playback_worker():
    """
    Continuously monitors the rotation_counts queue and handles playback.
    Allows interruptions to switch categories dynamically.
    """
    current_category_id = None
    last_rotation_count = None
    is_playing = False

    while True:
        if not rotation_counts.empty():
            new_category_id = rotation_counts.get()

            # Debounce to prevent repeated triggers
            if new_category_id == last_rotation_count:
                continue
            last_rotation_count = new_category_id

            # Stop current playback and switch to the new category
            if new_category_id != current_category_id:
                if is_playing:
                    print("Interrupting current playback to switch category.")
                    stop_current_audio()
                    is_playing = False

                current_category_id = new_category_id
                print(f"Switching to category: {current_category_id}")
                playback_audio_with_navigation(current_category_id, "topic", DB_PATH)
                is_playing = True

# The rest of the functions remain unchanged (serial_worker, etc.).
# Threads
serial_thread = Thread(target=serial_worker, args=("COM8 ",), daemon=True)
playback_thread = Thread(target=playback_worker, daemon=True)

# Start threads
serial_thread.start()
playback_thread.start()

# Keep the main thread alive
try:
    print("Playback Bridge is running. Press Ctrl+C to exit.")
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Exiting Playback Bridge.")
