import os
import time
import requests
import numpy as np
from io import BytesIO
from elevenlabs import ElevenLabs
from openai import OpenAI
from datetime import datetime
import sqlite3
from dotenv import load_dotenv
load_dotenv()

OPENAI_API_KEY = "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"
ELEVENLABS_API_KEY ="sk_870a763612522937db97dc08e24c2ed4543bc05c9343c110"


# Path to the database
DB_PATH = r"C:\Users\relle\OneDrive\Desktop\Agora\Database\MemoriaFM.db"
AUDIO_FOLDER_PATH = r"C:\Users\relle\OneDrive\Desktop\Agora\Audio_Recordings"
VOICE_ID = "EXAVITQu4vr4xnSDxMaL"   # Replace with the desired voice ID
MODEL_ID = "eleven_multilingual_v2"

def normalize_file_name(file_name):
    """
    Normalize the file name to a consistent format.
    For example, convert to lowercase.
    """
    return file_name.lower()


# Function to connect to the database
def connect_to_db(db_path):
    conn = sqlite3.connect(db_path)
    return conn

def process_audio_folder(folder_path, db_path):
    print(f"process_audio_folder called with folder_path: {folder_path}")
    ...
    print(f"Contents of folder {folder_path}: {os.listdir(folder_path)}")
    ...
    def normalize_file_name(file_name):
        return file_name.lower()

    print(f"Scanning folder: {folder_path}")
    if not os.path.exists(folder_path):
        print(f"Error: Path does not exist: {folder_path}")
        return
    if not os.path.isdir(folder_path):
        print(f"Error: Path is not a directory: {folder_path}")
        return
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".m4a"):
            normalized_name = normalize_file_name(file_name)
            print(f"Checking processed status for: {normalized_name}")
            if is_file_processed(db_path, normalized_name):
                print(f"Skipping processed file: {normalized_name}")
                continue
            print(f"File is new and will be processed: {normalized_name}")
            file_path = os.path.join(folder_path, file_name)
            process_audio_and_store_with_category(file_path, db_path)
            mark_file_as_processed(db_path, normalized_name)

def is_file_processed(db_path, file_name):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM processed_files WHERE file_name = ?", (file_name,))
    result = cursor.fetchone()
    conn.close()
    print(f"Checked file: {file_name}, Processed: {result is not None}")
    return result is not None

def mark_file_as_processed(db_path, file_name):
    normalized_name = normalize_file_name(file_name)  # Use the global function
    print(f"Marking file as processed: {normalized_name}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO processed_files (file_name) VALUES (?)", (normalized_name,))
    conn.commit()
    conn.close()

# Function to calculate cosine similarity
def cosine_similarity(vec1, vec2):
    dot_product = np.dot(vec1, vec2)
    norm_vec1 = np.linalg.norm(vec1)
    norm_vec2 = np.linalg.norm(vec2)
    return dot_product / (norm_vec1 * norm_vec2)
# Function to generate an embedding for the transcription

def generate_embedding(text, model="text-embedding-ada-002"):
    """
    Generate an embedding for the given text using OpenAI's embedding endpoint via HTTPS.
    """
    url = "https://api.openai.com/v1/embeddings"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "input": text,
        "model": "text-embedding-3-large"
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Raise an error for HTTP issues
        embedding = response.json()["data"][0]["embedding"]
        print(f"Generated embedding for text: {text[:50]}...")
        return np.array(embedding, dtype=np.float32)
    except requests.exceptions.RequestException as e:
        print(f"HTTP error occurred while generating embedding: {e}")
        return None

def transcribe_audio(file_path):
    """
    Transcribe audio using OpenAI's Whisper model via HTTPS.
    """
    url = "https://api.openai.com/v1/audio/transcriptions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    data = {
        "model": "whisper-1"
    }

    try:
        # Open the audio file in binary mode
        with open(file_path, "rb") as audio_file:
            # Make the HTTPS POST request
            response = requests.post(url, headers=headers, data=data, files={"file": audio_file})
            response.raise_for_status()  # Raise an error for HTTP issues

            # Extract the transcription text from the response
            transcription = response.json()["text"]
            print(f"Transcription: {transcription[:50]}...")
            return transcription
    except requests.exceptions.RequestException as e:
        print(f"HTTP error occurred while transcribing audio: {e}")
        return None
    except KeyError:
        print("Unexpected response format from OpenAI.")
        return None

def generate_category_name(transcription):
    try:
        # OpenAI API endpoint
        url = "https://api.openai.com/v1/chat/completions"

        # Headers for the HTTPS request
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }

        # Data payload for the HTTPS request
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": "You are an assistant tasked with creating meaningful, concise category names based on text."
                },
                {
                    "role": "user",
                    "content": f"Suggest a relevant two-word name for this text: {transcription}"
                }
            ],
            "max_tokens": 10,
            "temperature": 0.7
        }

        # Make the HTTPS request
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Raise an error for HTTP issues

        # Parse the JSON response
        category_name = response.json()["choices"][0]["message"]["content"].strip()
        print(f"Generated category name: {category_name}")
        return category_name

    except requests.exceptions.RequestException as e:
        print(f"HTTP error occurred while generating category name: {e}")
        return "Unnamed Category"
    except KeyError:
        print("Unexpected response format from OpenAI.")
        return "Unnamed Category"

def create_new_category(db_path, embedding, transcription):
    """
    Create a new category in the database and generate its audio name.
    """
    # Step 1: Generate a category name using the transcription
    category_name = generate_category_name(transcription)

    # Step 2: Define the audio file path
    sanitized_name = category_name.replace(" ", "_").lower()
    base_dir = r"C:\Users\relle\OneDrive\Desktop\Agora\CategoryAudio"

    audio_file_path = os.path.join(base_dir, f"{sanitized_name}.mp3")

    # Ensure the audio directory exists
    os.makedirs(os.path.dirname(audio_file_path), exist_ok=True)

    # Step 3: Generate the category name audio
    generate_category_audio(category_name, audio_file_path)

    # Step 4: Insert the new category into the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    serialized_embedding = embedding.tobytes()
    cursor.execute('''
        INSERT INTO categories (name, embedding, name_audio_path)
        VALUES (?, ?, ?)
    ''', (category_name, sqlite3.Binary(serialized_embedding), audio_file_path))
    conn.commit()
    new_category_id = cursor.lastrowid
    conn.close()

    print(f"Created new category: {category_name} (ID {new_category_id}) with audio path '{audio_file_path}'")
    return new_category_id

def assign_or_create_category(db_path, embedding, transcription, threshold=0.50):
    """
    Assign a recording to an existing category or create a new category.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Fetch all categories
    cursor.execute('SELECT id, name, embedding FROM categories')
    categories = cursor.fetchall()

    # Compare with existing categories
    for category in categories:
        category_id = category[0]
        category_name = category[1]
        category_embedding = np.frombuffer(category[2], dtype=np.float32)

        similarity = cosine_similarity(embedding, category_embedding)
        print(f"Similarity with category '{category_name}' (ID {category_id}): {similarity}")

        if similarity >= threshold:
            conn.close()
            print(f"Matched existing category: {category_name} (ID {category_id})")
            return category_id

    # If no match found, create a new category
    conn.close()
    return create_new_category(db_path, embedding, transcription)

# Function to store the recording's metadata into the database
def save_to_recordings(db_path, transcription, embedding, category_id, file_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    creation_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    serialized_embedding = embedding.tobytes()

    cursor.execute('''
        INSERT INTO recordings (transcription, embedding, creation_date, category_id, file_path)
        VALUES (?, ?, ?, ?, ?)
    ''', (transcription, sqlite3.Binary(serialized_embedding), creation_date, category_id, file_path))

    conn.commit()
    conn.close()
    print(f"Recording metadata with file_path '{file_path}' successfully inserted into the database.")

# Function to update the category_id in the recordings table
def update_recording_category(db_path, recording_id, category_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE recordings
        SET category_id = ?
        WHERE id = ?
    ''', (category_id, recording_id))
    conn.commit()
    conn.close()
    print(f"Recording ID {recording_id} updated with Category ID {category_id}.")

def generate_category_audio(category_name, output_file):
    """
    Generate audio for the category name using the ElevenLabs SDK and save to a file.
    """
    try:
        if not ELEVENLABS_API_KEY:
            raise ValueError("ElevenLabs API key is missing.")

        print(f"Generating audio for category '{category_name}' with output to '{output_file}'.")

        client = ElevenLabs(api_key=ELEVENLABS_API_KEY)  # Ensure ElevenLabs is correctly imported
        audio_generator = client.text_to_speech.convert(
            voice_id=VOICE_ID,
            model_id=MODEL_ID,
            text=category_name,
        )

        # Save the audio data to the file
        with open(output_file, "wb") as f:
            for chunk in audio_generator:
                f.write(chunk)  # Write each chunk of audio data
        print(f"Audio for category '{category_name}' saved to {output_file}")
    except Exception as e:
        print(f"Error generating audio for category '{category_name}': {e}")
        raise

def process_audio_and_store_with_category(file_path, db_path):
    # Step 1: Transcribe the audio
    transcription = transcribe_audio(file_path)
    if not transcription:
        print("Error: Could not transcribe audio.")
        return

    print(f"Transcription: {transcription}")

    # Step 2: Generate the embedding
    embedding = generate_embedding(transcription)
    if embedding is None:
        print("Error: Could not generate embedding.")
        return

    # Step 3: Assign or create a category
    category_id = assign_or_create_category(db_path, embedding, transcription)

    # Step 4: Save the recording metadata, including file_path
    save_to_recordings(db_path, transcription, embedding, category_id, file_path)

def check_processed_files_table(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM processed_files")
    rows = cursor.fetchall()
    conn.close()
    for row in rows:
        print(f"Processed file: {row[0]}")
    return rows

check_processed_files_table(DB_PATH)

print(f"Database Path: {DB_PATH}")
print(f"Audio Folder Path: {AUDIO_FOLDER_PATH}")
process_audio_folder(AUDIO_FOLDER_PATH, DB_PATH)



